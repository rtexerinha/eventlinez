import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

from cart.models import Cart
from cart.views import _cart_id
from order.tasks import send_mail
from ticket.models import Ticket
from .models import Order
from .models import OrderItem
from promoter.models import PromoCode, PromoCodeUsage
from django.db import transaction

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return JsonResponse({'error': 'Invalid signature'}, status=400)

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        logger.info(f"Checkout session completed: {session}")
        # Add your logic here (e.g., update order status, send email)

    elif event['type'] == 'checkout.session.async_payment_succeeded':
        session = event['data']['object']
        logger.info(f"Async payment succeeded: {session}")
        # Add your logic here

    elif event['type'] == 'checkout.session.async_payment_failed':
        session = event['data']['object']
        logger.warning(f"Async payment failed: {session}")
        # Add your logic here

    return JsonResponse({'status': 'success'})


@login_required()
def thanks(request, order_id):
    try:
        customer_order = None
        tickets = None
        if order_id:
            try:
                customer_order = get_object_or_404(Order, id=order_id)
                print(f"Displaying thanks page for order: {customer_order.id}")
                
                # Verify the order belongs to the current user
                if customer_order.customer != request.user.customer:
                    print(f"ERROR: Order {order_id} does not belong to user {request.user.username}")
                    return render(request, 'order/error.html', {
                        'error': 'Order not found or access denied.',
                        'PROD': settings.PROD
                    })
                
                tickets = Ticket.objects.filter(order_item__order=customer_order).order_by('created_at')
                print(f"Found {tickets.count()} tickets for order {order_id}")
            except Exception as e:
                print(f"ERROR: Failed to retrieve order {order_id}: {e}")
                return render(request, 'order/error.html', {
                    'error': f'Unable to retrieve order details: {e}',
                    'PROD': settings.PROD
                })
        
        return render(request, 'thanks.html', {
            'customer_order': customer_order, 
            'tickets': tickets, 
            'PROD': settings.PROD
        })
    except Exception as e:
        print(f"CRITICAL ERROR in thanks view: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'order/error.html', {
            'error': f'An unexpected error occurred: {e}',
            'PROD': settings.PROD
        })


@login_required()
def order_list(request):
    try:
        email = str(request.user.username)
        print(f"Retrieving orders for user: {email}")
        
        try:
            orders = Order.objects.filter(emailAddress=email).order_by('-id')
            print(f"Found {orders.count()} orders for user {email}")
        except Exception as e:
            print(f"ERROR: Failed to retrieve orders for {email}: {e}")
            return render(request, 'order/error.html', {
                'error': f'Unable to retrieve order history: {e}',
                'PROD': settings.PROD
            })
        
        return render(request, 'order/orders_list.html', {
            'orders': orders, 
            'PROD': settings.PROD
        })
    except Exception as e:
        print(f"CRITICAL ERROR in order_list view: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'order/error.html', {
            'error': f'An unexpected error occurred: {e}',
            'PROD': settings.PROD
        })


@login_required()
def order_detail(request, order_id):
    try:
        print(f"Retrieving order details for order: {order_id}")
        
        try:
            order = get_object_or_404(Order, id=order_id)
            
            # Verify the order belongs to the current user
            if order.customer != request.user.customer:
                print(f"ERROR: Order {order_id} does not belong to user {request.user.username}")
                return render(request, 'order/error.html', {
                    'error': 'Order not found or access denied.',
                    'PROD': settings.PROD
                })
            
            print(f"Retrieved order: {order.id} for user {request.user.username}")
            
        except Exception as e:
            print(f"ERROR: Failed to retrieve order {order_id}: {e}")
            return render(request, 'order/error.html', {
                'error': f'Order not found: {e}',
                'PROD': settings.PROD
            })
        
        return render(request, 'order/order_detail.html', {
            'order': order, 
            'PROD': settings.PROD
        })
    except Exception as e:
        print(f"CRITICAL ERROR in order_detail view: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'order/error.html', {
            'error': f'An unexpected error occurred: {e}',
            'PROD': settings.PROD
        })


@login_required()
def create(request):
    try:
        # Get session_id and validate
        session_id = request.GET.get('session_id')
        print(f"Processing order for session_id: {session_id}")
        
        if not session_id:
            print("ERROR: No session_id provided")
            return render(request, 'order/error.html', {
                'error': 'No payment session ID provided',
                'PROD': settings.PROD
            })

        # Get cart
        try:
            cart_id = _cart_id(request)
            cart = Cart.objects.get(cart_id=cart_id)
            print(f"Found cart: {cart.id} with {cart.cartitem_set.count()} items")
        except Cart.DoesNotExist:
            print(f"ERROR: Cart not found for cart_id: {cart_id}")
            return render(request, 'order/error.html', {
                'error': 'Shopping cart not found. Please try again.',
                'PROD': settings.PROD
            })
        except Exception as e:
            print(f"ERROR: Failed to get cart: {e}")
            return render(request, 'order/error.html', {
                'error': f'Cart error: {e}',
                'PROD': settings.PROD
            })

        # Set Stripe API key and retrieve session
        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session = stripe.checkout.Session.retrieve(session_id)
            print(f"Retrieved Stripe session: {session.id}, status: {session.payment_status}")
        except stripe.error.InvalidRequestError as e:
            print(f"ERROR: Invalid Stripe session: {e}")
            return render(request, 'order/error.html', {
                'error': 'Invalid payment session. Please try again.',
                'PROD': settings.PROD
            })
        except Exception as e:
            print(f"ERROR: Failed to retrieve Stripe session: {e}")
            return render(request, 'order/error.html', {
                'error': f'Payment verification failed: {e}',
                'PROD': settings.PROD
            })

        # Validate payment status
        if session.payment_status != "paid":
            print(f"ERROR: Payment not completed. Status: {session.payment_status}")
            return render(request, 'order/error.html', {
                'error': f'Payment not completed. Status: {session.payment_status}',
                'PROD': settings.PROD
            })

        # Validate cart reference
        if session.client_reference_id != str(cart.id):
            print(f"ERROR: Cart ID mismatch. Session: {session.client_reference_id}, Cart: {cart.id}")
            return render(request, 'order/error.html', {
                'error': 'Payment session does not match your cart. Please contact support.',
                'PROD': settings.PROD
            })

        # Check if user has customer profile
        try:
            customer = request.user.customer
            print(f"Found customer: {customer.email}")
        except Exception as e:
            print(f"ERROR: User has no customer profile: {e}")
            return render(request, 'order/error.html', {
                'error': 'Customer profile not found. Please complete your profile.',
                'PROD': settings.PROD
            })

        # Create order
        try:
            order = Order.objects.create(
                total=cart.amount(),
                emailAddress=customer.email,
                customer=customer,
                token=session_id,
                payment_code=session.payment_intent
            )
            print(f"Created order: {order.id}")
        except Exception as e:
            print(f"ERROR: Failed to create order: {e}")
            return render(request, 'order/error.html', {
                'error': f'Failed to create order: {e}',
                'PROD': settings.PROD
            })

        # Get cart items
        try:
            items = cart.cartitem_set.filter(active=True)
            if not items.exists():
                print("ERROR: No active items in cart")
                return render(request, 'order/error.html', {
                    'error': 'No items found in cart',
                    'PROD': settings.PROD
                })
            print(f"Processing {items.count()} cart items")
        except Exception as e:
            print(f"ERROR: Failed to get cart items: {e}")
            return render(request, 'order/error.html', {
                'error': f'Cart items error: {e}',
                'PROD': settings.PROD
            })

        # Update Stripe PaymentIntent with order metadata and comprehensive description
        try:
            from order.stripe_utils import build_stripe_description, build_stripe_metadata_from_order
            
            # Build comprehensive description with event name and order number
            first_item = items.first()
            if first_item:
                event_name = first_item.ticket.event.name
                tier_name = first_item.ticket.name
                description = build_stripe_description(event_name, tier_name, order_id=order.id)
            else:
                description = f"Order #{order.id}"
            
            # Build comprehensive metadata using helper function
            metadata = build_stripe_metadata_from_order(order)
            
            stripe.PaymentIntent.modify(
                session.payment_intent,
                metadata=metadata,
                description=description
            )
            print(f"Updated Stripe PaymentIntent {session.payment_intent} with description: {description}")
        except Exception as e:
            print(f"WARNING: Failed to update Stripe metadata: {e}")
            import traceback
            traceback.print_exc()
            # Continue anyway as this is not critical

        # Create order items
        order_items_created = 0
        for item in items:
            try:
                OrderItem.objects.create(
                    event_ticket=item.ticket,
                    quantity=item.quantity,
                    unit_price=item.ticket.price,
                    amount=item.price_total(),
                    fee=item.fee(),
                    promo_code=item.promo_code,
                    order=order,
                    vendor=item.vendor
                )
                order_items_created += 1
                print(f"Created order item: {item.ticket.name}")
            except Exception as e:
                print(f"ERROR: Failed to create order item for {item.ticket}: {e}")
                # Continue with other items

        if order_items_created == 0:
            print("ERROR: Failed to create any order items")
            return render(request, 'order/error.html', {
                'error': 'Failed to process any order items',
                'PROD': settings.PROD
            })

        print(f"Successfully created {order_items_created} order items")

        # Track promo code usage — collect unique codes from the cart items
        try:
            promo_codes_used = set(
                item.promo_code for item in items if item.promo_code
            )
            for code in promo_codes_used:
                with transaction.atomic():
                    promo = PromoCode.objects.select_for_update().get(code=code)
                    # Avoid double-counting if order is somehow processed twice
                    already_recorded = PromoCodeUsage.objects.filter(
                        promo_code=promo,
                        order_id=str(order.id)
                    ).exists()
                    if not already_recorded:
                        PromoCodeUsage.objects.create(
                            promo_code=promo,
                            customer_email=customer.email,
                            order_id=str(order.id),
                            discount_amount=cart.promo_discount or 0,
                        )
                        # Use F() to avoid race condition on concurrent purchases
                        from django.db.models import F
                        PromoCode.objects.filter(pk=promo.pk).update(
                            current_uses=F('current_uses') + 1
                        )
                        logger.info(f"Promo code '{code}' usage recorded for order {order.id}")
        except PromoCode.DoesNotExist:
            logger.warning(f"Promo code '{code}' not found during usage tracking")
        except Exception as e:
            logger.error(f"Failed to track promo code usage for order {order.id}: {e}")
            # Non-critical — order is already created, don't block the customer

        # Delete cart
        try:
            cart.delete()
            print("Cart deleted successfully")
        except Exception as e:
            print(f"WARNING: Failed to delete cart: {e}")
            # Continue anyway

        # Send confirmation email
        try:
            send_mail(order.id)
            print("Confirmation email sent")
        except Exception as e:
            print(f"WARNING: Failed to send confirmation email: {e}")
            # Continue anyway

        print(f"Order {order.id} processed successfully")
        return redirect('order:thanks', order.id)

    except Exception as e:
        print(f"CRITICAL ERROR in order creation: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'order/error.html', {
            'error': f'An unexpected error occurred: {e}',
            'PROD': settings.PROD
        })
