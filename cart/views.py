import logging
import json
from datetime import timedelta

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from event.models import Ticket
from promoter.models import Vendor, PromoCode, PromoCodeUsage
from .models import Cart, CartItem
from .utils import track_cart_abandonment, mark_cart_converted
from django.conf import settings

from django.contrib import messages 
from .rate_limiting import rate_limit, get_cart_identifier, get_item_identifier, get_ticket_identifier

logger = logging.getLogger(__name__)

# A second checkout of the exact same tickets by the same customer within this
# window is treated as an accidental double-purchase, not a deliberate one.
DUPLICATE_ORDER_WINDOW_MINUTES = 15


def _cart_signature(items):
    """A comparable fingerprint of a cart's contents: sorted (ticket_id, quantity)."""
    return sorted((item.ticket_id, item.quantity) for item in items)


def _find_recent_duplicate_order(customer, items):
    """
    Return a recent PAID order belonging to `customer` whose items exactly match
    the current cart (same tickets, same quantities), created within
    DUPLICATE_ORDER_WINDOW_MINUTES. Used to stop an accidental second charge when
    a customer who didn't see a confirmation retries the same purchase.

    Returns the matching Order or None.
    """
    from order.models import Order

    cart_sig = _cart_signature(items)
    cutoff = timezone.now() - timedelta(minutes=DUPLICATE_ORDER_WINDOW_MINUTES)
    recent_orders = (
        Order.objects.filter(
            customer=customer,
            status=Order.STATUS_PAID,
            created__gte=cutoff,
        )
        .prefetch_related('orderitem_set')
    )
    for order in recent_orders:
        order_sig = sorted(
            (oi.event_ticket_id, oi.quantity) for oi in order.orderitem_set.all()
        )
        if order_sig == cart_sig:
            return order
    return None


def _cart_id(request):
    try:
        if not hasattr(request, 'session'):
            return None
        if not request.session.session_key:
            request.session.create()
        return request.session.session_key
    except Exception:
        # Return a fallback cart ID if session fails
        return f"fallback_{request.META.get('REMOTE_ADDR', 'unknown')}"


def _clear_cart_promo(cart):
    """
    Clear any applied promo code from the cart and all its items.
    Returns True if a promo was actually cleared, False if there was nothing to clear.
    Must be called whenever the cart contents change so the discount is never based
    on a stale subtotal.
    """
    if not cart.applied_promo_code:
        return False
    cart.applied_promo_code = None
    cart.promo_discount = 0
    cart.save(update_fields=['applied_promo_code', 'promo_discount'])
    CartItem.objects.filter(cart=cart).update(promo_code=None)
    return True


def track_promo_usage(promo_code, customer_email, order_id, discount_amount):
    """
    Track promo code usage and update usage count
    """
    try:
        with transaction.atomic():
            # Get the promo code
            promo = PromoCode.objects.select_for_update().get(code=promo_code)
            
            # Create usage record
            PromoCodeUsage.objects.create(
                promo_code=promo,
                customer_email=customer_email,
                order_id=order_id,
                discount_amount=discount_amount
            )
            
            # Increment usage count
            promo.current_uses += 1
            promo.save()
            
            logger.info(f"Promo code usage tracked: {promo_code} used by {customer_email}")
            
    except PromoCode.DoesNotExist:
        logger.error(f"Promo code not found for usage tracking: {promo_code}")
    except Exception as e:
        logger.error(f"Error tracking promo code usage: {e}")


@csrf_exempt
@rate_limit('cart_add', identifier_func=get_ticket_identifier)
def cart_add(request):
    """
    Adiciona cria o carrinho e adiciona os tickets ao carrinho.
    """
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        # Ensure we have a session
        if not request.session.session_key:
            request.session.create()
        
        cart_id = _cart_id(request)
        cart, created = Cart.objects.get_or_create(cart_id=cart_id)
        
        if created:
            cart.save()
            logger.info(f"Created new cart with ID: {cart_id}")

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        
        promocode = data.get("promo_code")
        vendor_code = data.get("vendor_code")
        tickets_data = data.get("tickets", [])

        if not tickets_data:
            return JsonResponse({"error": "No tickets provided"}, status=400)

        vendor = None
        if vendor_code:
            try:
                vendor = Vendor.objects.get(code=vendor_code)
            except Vendor.DoesNotExist:
                return JsonResponse({"error": "Invalid vendor code"}, status=400)

        items_added = 0
        for tkt in tickets_data:
            try:
                ticket = Ticket.objects.get(pk=tkt['id'])
            except Ticket.DoesNotExist:
                return JsonResponse({"error": f"Ticket with ID {tkt['id']} not found"}, status=400)
            except KeyError:
                return JsonResponse({"error": "Ticket ID is required"}, status=400)
            
            try:
                quantity = int(tkt['quantity'])
            except (KeyError, ValueError, TypeError):
                return JsonResponse({"error": "Valid quantity is required"}, status=400)

            if quantity == 0:
                continue
            if quantity < 0:
                return JsonResponse({"error": "Quantity cannot be negative"}, status=400)
            
            qtd_available = ticket.qty_available()
            if quantity > qtd_available:
                return JsonResponse({
                    "error": f"Quantity cannot be greater than {qtd_available} for ticket '{ticket.name}'"
                }, status=400)

            # Check if item already exists in cart
            existing_item = cart.cartitem_set.filter(ticket=ticket).first()
            if existing_item and existing_item.quantity > 0:
                new_quantity = existing_item.quantity + quantity
                if new_quantity > qtd_available:
                    return JsonResponse({
                        "error": f"Total quantity would exceed available tickets ({qtd_available}) for '{ticket.name}'"
                    }, status=400)
                existing_item.quantity = new_quantity
                existing_item.save()
                logger.info(f"Updated existing cart item: ticket {ticket.id}, new quantity: {new_quantity}")
            else:
                CartItem.objects.create(
                    ticket=ticket,
                    cart=cart,
                    quantity=quantity,
                    promo_code=promocode,
                    vendor=vendor
                )
                logger.info(f"Created new cart item: ticket {ticket.id}, quantity: {quantity}")
            
            items_added += 1

        if items_added == 0:
            return JsonResponse({"error": "No valid tickets were added to cart"}, status=400)

        # Start / reset the 5-minute reservation timer every time items are added
        cart.reserved_at = timezone.now()
        cart.save(update_fields=['reserved_at'])

        # If the user previously reached Stripe then came back and changed the cart,
        # the old Stripe session no longer matches — force a fresh one on next checkout.
        request.session.pop(f'pending_stripe_session_{cart.id}', None)

        promo_cleared = _clear_cart_promo(cart)
        return JsonResponse({
            "status": "success",
            "message": f"Added {items_added} item{'s' if items_added != 1 else ''} to cart",
            "cart_id": cart.id,
            "promo_cleared": promo_cleared,
            "reservation_seconds": Cart.RESERVATION_MINUTES * 60,
        }, status=201)

    except Exception as e:
        logger.error(f"Error adding items to cart: {e}")
        return JsonResponse({"error": "An error occurred while adding items to cart"}, status=500)


@login_required()
@rate_limit('quantity_change', identifier_func=get_item_identifier)
def change_quantity(request, item_id, operation):
    """
    Altera a quantidade de um item no carrinho
    :param request
    :param item_id: Id do item que terá a quantidade alterada
    :param operation: Operação que será realizada
    :return:
    """
    item = get_object_or_404(CartItem, id=item_id)

    if operation == 'increment':
        if item.quantity < item.ticket.qty_available():
            item.quantity += 1

    if operation == 'decrement':
        if item.quantity > 1:
            item.quantity -= 1

    item.save()
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        request.session.pop(f'pending_stripe_session_{cart.id}', None)
        if _clear_cart_promo(cart):
            messages.info(request, "Promo code removed — please re-apply to recalculate your discount.")
    except Cart.DoesNotExist:
        pass
    return redirect('cart:detail')


def cart_detail(request, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))

        if cart.is_expired():
            cart.clear_items()
            request.session.pop(f'pending_stripe_session_{cart.id}', None)
            messages.warning(request, 'Your reservation expired. Please add tickets again.')

        all_items = CartItem.objects.filter(cart=cart, active=True)
        sold_out_items = all_items.filter(ticket__sold_out=True)

        if sold_out_items.exists():
            sold_out_names = [item.ticket.name for item in sold_out_items]
            messages.warning(request, "The following items are no longer available: " + ", ".join(sold_out_names))
        
        cart_items = all_items.exclude(ticket__sold_out=True)

        promo_code = cart_items.first().promo_code if cart_items.exists() else None
        subtotal = sum(item.price_total() for item in cart_items)
        
        # Calculate total - always use cart.total_with_promo() if there's an applied promo code
        if cart.applied_promo_code:
            total = cart.total_with_promo()
        else:
            total = subtotal

        from decimal import Decimal
        total = Decimal(str(total)) if total else Decimal('0.00')
        subtotal = Decimal(str(subtotal)) if subtotal else Decimal('0.00')

    except Cart.DoesNotExist:
        logger.error("The cart does not exist.")
        cart_items = []
        promo_code = None
        from decimal import Decimal
        subtotal = Decimal('0.00')
        total = Decimal('0.00')
        cart = None
        seconds_remaining = 0

    # Track cart abandonment if user has items in cart
    if cart_items and request.user.is_authenticated:
        try:
            customer_email = getattr(request.user, 'email', '')
            if not customer_email and hasattr(request.user, 'customer'):
                customer_email = request.user.customer.email
            
            track_cart_abandonment(
                cart_id=_cart_id(request),
                user=request.user,
                email=customer_email
            )
        except Exception as e:
            logger.warning(f"Failed to track cart abandonment: {e}")

    seconds_remaining = cart.seconds_remaining if cart else 0

    context = {
        'total': total,
        'subtotal': subtotal,
        'cart_items': cart_items,
        'promo_code': promo_code,
        'cart': cart,
        'reservation_seconds': seconds_remaining,
        'PROD': settings.PROD,
    }
    
    response = render(request, 'cart.html', context)
    # Prevent bfcache on mobile Safari / in-app browsers. Without no-store, the
    # browser freezes a snapshot of the cart page before redirecting to Stripe.
    # Hitting back restores that snapshot (stale items, old total, old promo) even
    # though the server already cleared the cart — leading to duplication on re-add.
    response['Cache-Control'] = 'no-store'
    return response


@rate_limit('item_remove', identifier_func=get_item_identifier)
def remove_item(request, item_id):
    """
    Remove um item do carrinho
    :param request
    :param item_id: Id do item que será removido
    :return:
    """
    item = get_object_or_404(CartItem, id=item_id)
    cart = item.cart
    item.delete()
    request.session.pop(f'pending_stripe_session_{cart.id}', None)
    if _clear_cart_promo(cart):
        messages.info(request, "Promo code removed — please re-apply to recalculate your discount.")
    return redirect('cart:detail')


@csrf_exempt
@rate_limit('promo_apply', identifier_func=get_cart_identifier)
def apply_promo_code(request):
    """
    Apply a promo code to the cart
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        promo_code = data.get('promo_code', '').upper().strip()
        
        if not promo_code:
            return JsonResponse({'error': 'Please enter a promo code'}, status=400)
        
        # Get cart
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        
        if not cart_items.exists():
            return JsonResponse({'error': 'Your cart is empty'}, status=400)
        
        # Find promo code - it should be for one of the events in the cart
        event_ids = cart_items.values_list('ticket__event_id', flat=True).distinct()
        event_names = list(cart_items.values_list('ticket__event__name', flat=True).distinct())
        
        logger.info(f"Cart has events: {event_names}")
        logger.info(f"Looking for promo code '{promo_code}' for event IDs: {list(event_ids)}")
        
        try:
            promo = PromoCode.objects.get(code=promo_code, event_id__in=event_ids)
        except PromoCode.DoesNotExist:
            # Check if promo code exists for other events
            existing_promo = PromoCode.objects.filter(code=promo_code).first()
            if existing_promo:
                return JsonResponse({
                    'error': f'Promo code "{promo_code}" is valid for "{existing_promo.event.name}" but your cart contains tickets for: {", ".join(event_names)}'
                }, status=400)
            else:
                return JsonResponse({'error': f'Promo code "{promo_code}" not found'}, status=400)
        
        # Validate promo code
        customer_email = ''
        if request.user.is_authenticated:
            customer_email = getattr(request.user, 'email', '')
            if not customer_email and hasattr(request.user, 'customer'):
                customer_email = request.user.customer.email
        else:
            # For unauthenticated users, use session-based email or session ID
            if not request.session.session_key:
                request.session.create()
            customer_email = request.session.session_key or ''
            
        can_use, message = promo.can_be_used_by_customer(customer_email)
        if not can_use:
            return JsonResponse({'error': message}, status=400)
        
        # Calculate discount
        subtotal = cart.subtotal()
        discount_amount = promo.calculate_discount(subtotal)
        
        # Apply promo code to cart
        cart.applied_promo_code = promo_code
        cart.promo_discount = discount_amount
        cart.save()
        
        # Update all cart items with the promo code
        cart_items.update(promo_code=promo_code)
        
        new_total = cart.total_with_promo()
        
        logger.info(f"Applied promo code '{promo_code}' to cart {cart.cart_id}: discount ${discount_amount}")
        
        return JsonResponse({
            'success': True,
            'message': f'Promo code "{promo_code}" applied successfully!',
            'discount_amount': float(discount_amount),
            'discount_display': promo.get_discount_display(),
            'new_total': float(new_total),
            'subtotal': float(subtotal)
        })
        
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=400)
    except Exception as e:
        logger.error(f"Error applying promo code: {e}")
        return JsonResponse({'error': 'An error occurred while applying the promo code'}, status=500)


@csrf_exempt
@rate_limit('promo_apply', identifier_func=get_cart_identifier)
def remove_promo_code(request):
    """
    Remove promo code from cart
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        
        # Remove promo code from cart
        cart.applied_promo_code = None
        cart.promo_discount = 0
        cart.save()
        
        # Remove promo code from cart items
        CartItem.objects.filter(cart=cart, active=True).update(promo_code=None)
        
        subtotal = cart.subtotal()
        
        return JsonResponse({
            'success': True,
            'message': 'Promo code removed successfully!',
            'new_total': float(subtotal),
            'subtotal': float(subtotal)
        })
        
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=400)
    except Exception as e:
        logger.error(f"Error removing promo code: {e}")
        return JsonResponse({'error': 'An error occurred while removing the promo code'}, status=500)


@csrf_exempt
@rate_limit('cart_checkout', identifier_func=get_cart_identifier)
def checkout(request):
    """
    Faz o redirecionamento do carrinho para processo de checkout no Stripe
    """
    # Return JSON 401 for unauthenticated AJAX requests instead of HTML redirect
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required', 'login_url': '/accounts/login/?next=/cart/'}, status=401)

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Cart not found. Please add items to your cart first.'}, status=400)

    items = CartItem.objects.filter(cart=cart, active=True)

    if not items.exists():
        return JsonResponse({'error': 'Your cart is empty.'}, status=400)

    if cart.is_expired():
        cart.clear_items()
        request.session.pop(f'pending_stripe_session_{cart.id}', None)
        return JsonResponse({
            'error': 'cart_expired',
            'message': 'Your reservation expired. Please add tickets again.',
        }, status=400)

    invalid_items = items.filter(ticket__sold_out=True)
    if invalid_items.exists():
        names = [item.ticket.name for item in invalid_items]
        return JsonResponse({'error': 'The following tickets are sold out: ' + ', '.join(names)}, status=400)

    # ── Duplicate-payment guard ──────────────────────────────────────────────
    # If this customer already completed an order for the exact same tickets in
    # the last few minutes, they almost certainly didn't see their confirmation
    # and are retrying. Send them to that order's thanks page instead of opening
    # a second Stripe session and charging them twice.
    try:
        customer = request.user.customer
    except Exception:
        customer = None

    try:
        body = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, Exception):
        body = {}
    force_new_purchase = body.get('force_new_purchase', False)

    if customer and not force_new_purchase:
        duplicate_order = _find_recent_duplicate_order(customer, items)
        if duplicate_order:
            logger.warning(
                f"Duplicate checkout blocked for customer {customer.id} "
                f"({customer.email}): cart matches existing order {duplicate_order.id} "
                f"created at {duplicate_order.created} — redirecting to thanks instead of re-charging"
            )
            return JsonResponse({
                'duplicate': True,
                'message': (
                    'You have already purchased these tickets. '
                    'Redirecting you to your confirmation.'
                ),
                'redirect_url': reverse('order:thanks', args=[duplicate_order.id]),
            }, status=200)

    # Check if Stripe is properly configured with real keys
    if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY in [
        'sk_test_51234567890abcdef',
        'sk_live_51H1234567890abcdef',
        'sk_test_placeholder',
        'sk_live_placeholder'
    ]:
        return JsonResponse({
            'error': 'Payment processing is not available. Please contact administrator for checkout assistance.'
        }, status=500)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Guard against duplicate charges: if this user already has an open Stripe
    # session for this same cart, reuse it instead of creating a second charge.
    _pending_key = f'pending_stripe_session_{cart.id}'
    _pending_session_id = request.session.get(_pending_key)
    if _pending_session_id:
        try:
            _existing = stripe.checkout.Session.retrieve(_pending_session_id)
            if _existing.status == 'open':
                return JsonResponse({
                    'session_id': _existing.id,
                    'checkout_url': _existing.url,
                    'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
                })
        except Exception:
            pass  # session expired or invalid — fall through to create a new one
    line_items = []
    cents = 100

    try:
        # Use cart total with promo discount
        total_amount = cart.total_with_promo()

        if total_amount > 0:
            line_item = {
                'price_data': {
                    'product_data': {
                        'name': f'Event Tickets ({items.count()} item{"s" if items.count() != 1 else ""})',
                        'description': f'Cart total with {items.count()} ticket{"s" if items.count() != 1 else ""}'
                    },
                    'unit_amount': int(total_amount * cents),
                    'currency': 'usd'
                },
                'quantity': 1,
            }
            line_items.append(line_item)
        else:
            return JsonResponse({'error': 'Cart total cannot be zero or negative'}, status=400)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return JsonResponse({'error': f'Payment processing error: {str(e)}'}, status=500)

    try:
        from order.stripe_utils import build_stripe_description, build_stripe_metadata_from_cart

        customer_email = getattr(request.user, 'email', '') or ''
        if not customer_email and hasattr(request.user, 'customer'):
            customer_email = request.user.customer.email or ''

        first_item = items.first()
        if first_item:
            description = build_stripe_description(
                first_item.ticket.event.name,
                first_item.ticket.name,
                customer_email=customer_email,
            )
            metadata = build_stripe_metadata_from_cart(cart, items, customer_email=customer_email)
        else:
            description = customer_email or f"Event Tickets - {items.count()} items"
            metadata = {}

        if cart.applied_promo_code:
            metadata['promo_code'] = cart.applied_promo_code
            metadata['promo_discount'] = str(cart.promo_discount)

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/order/success/') + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('cart:stripe-cancel')),
            customer_email=customer_email or None,
            metadata=metadata,
            payment_intent_data={
                'description': description,
                'metadata': metadata
            },
            client_reference_id=cart.id,
            allow_promotion_codes=False
        )
    except stripe.error.StripeError as e:
        logger.error(f"Stripe session creation error: {e}")
        return JsonResponse({'error': f'Payment session creation failed: {str(e)}'}, status=500)

    # Reset the reservation clock at the moment the customer is sent to Stripe.
    # Without this, the 5-minute countdown (running in a background tab) could
    # expire and wipe cart items while the customer is filling in card details,
    # causing a "cart empty" error on the success URL even though payment succeeded.
    cart.reserved_at = timezone.now()
    cart.save(update_fields=['reserved_at'])

    # Store session ID in the user's Django session so a repeat checkout request
    # reuses the same Stripe session rather than creating a duplicate charge.
    request.session[f'pending_stripe_session_{cart.id}'] = session.id

    try:
        mark_cart_converted(cart.cart_id, order_id=session.id)
    except Exception as e:
        logger.warning(f"Failed to mark cart as converted: {e}")

    return JsonResponse({
        'session_id': session.id,
        'checkout_url': session.url,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


def stripe_cancel(request):
    """
    Stripe cancel_url target. Clears the cart and pending session so the
    customer starts fresh — prevents stale reservations and duplicate sessions.
    Redirects back to the event detail page so the customer can add tickets again.
    """
    event_url = None
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        first_item = CartItem.objects.filter(cart=cart, active=True).select_related(
            'ticket__event__category'
        ).first()
        if first_item:
            event = first_item.ticket.event
            event_url = reverse('shop:product_event_detail', kwargs={
                'c_slug': event.category.slug,
                'event_slug': event.slug,
            })
        request.session.pop(f'pending_stripe_session_{cart.id}', None)
        cart.clear_items()
        logger.info(f"Cart {cart.cart_id} cleared after Stripe cancel")
    except Cart.DoesNotExist:
        pass
    return redirect(event_url or reverse('index'))


@csrf_exempt
def expire_cart(request):
    """Called by the frontend countdown timer when the reservation window closes."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart.clear_items()
        request.session.pop(f'pending_stripe_session_{cart.id}', None)
        return JsonResponse({'status': 'expired'})
    except Cart.DoesNotExist:
        return JsonResponse({'status': 'already_empty'})
