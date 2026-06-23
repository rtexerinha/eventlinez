import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging

from cart.models import Cart
from order.tasks import send_mail
from ticket.models import Ticket, CancelledTicket
from .models import Order, OrderItem, TicketRefund
from promoter.models import PromoCode, PromoCodeUsage
from django.db import transaction
from decimal import Decimal

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

    try:
        if event['type'] == 'checkout.session.completed':
            _webhook_recover_order(event['data']['object'])

        elif event['type'] == 'charge.refunded':
            _webhook_handle_refund(event['data']['object'])

        elif event['type'] == 'checkout.session.async_payment_succeeded':
            logger.info(f"Async payment succeeded: {event['data']['object'].get('id')}")

        elif event['type'] == 'checkout.session.async_payment_failed':
            logger.warning(f"Async payment failed: {event['data']['object'].get('id')}")

    except Exception as e:
        logger.error(f"Webhook handler error for {event.get('type')}: {e}", exc_info=True)
        return JsonResponse({'error': 'handler_error'}, status=500)

    return JsonResponse({'status': 'success'})


def _webhook_recover_order(session):
    """
    Called from the stripe_webhook when checkout.session.completed fires.
    Creates the order if the success-URL redirect never completed (closed browser,
    lost session cookie, etc.).  Idempotent: if the redirect already created the
    order we skip silently.
    """
    session_id = session.get('id', '')

    # Idempotency — success URL already created the order
    if Order.objects.filter(token=session_id).exists():
        logger.info(f"Webhook: order already exists for session {session_id}, skipping")
        return

    if session.get('payment_status') != 'paid':
        logger.warning(
            f"Webhook: session {session_id} payment_status={session.get('payment_status')}, skipping"
        )
        return

    cart_id = session.get('client_reference_id')
    if not cart_id:
        logger.error(f"Webhook: no client_reference_id in session {session_id}")
        return

    try:
        cart = Cart.objects.get(id=cart_id)
    except Cart.DoesNotExist:
        logger.error(
            f"Webhook RECOVERY FAILED: cart {cart_id} already deleted for paid session "
            f"{session_id} (payment_intent={session.get('payment_intent')}) — manual recovery required"
        )
        return

    # Customer lookup by email from Stripe
    customer_details = session.get('customer_details') or {}
    customer_email = customer_details.get('email') or session.get('customer_email') or ''
    if not customer_email:
        logger.error(f"Webhook: no customer email in session {session_id}")
        return

    from customer.models import Customer as _Customer
    try:
        customer = _Customer.objects.get(email__iexact=customer_email.strip())
    except _Customer.DoesNotExist:
        logger.error(
            f"Webhook: customer with email '{customer_email}' not found for session {session_id}"
        )
        return

    items = cart.cartitem_set.filter(active=True)
    if not items.exists():
        logger.error(f"Webhook: cart {cart_id} has no active items for session {session_id}")
        return

    # Use the actual amount Stripe charged (in cents → dollars)
    stripe_total = Decimal(session.get('amount_total', 0)) / 100

    try:
        with transaction.atomic():
            order = Order.objects.create(
                total=stripe_total,
                emailAddress=customer.email,
                customer=customer,
                token=session_id,
                payment_code=session.get('payment_intent', ''),
            )
            for item in items:
                OrderItem.objects.create(
                    event_ticket=item.ticket,
                    quantity=item.quantity,
                    unit_price=item.ticket.price,
                    amount=item.price_total(),
                    fee=item.fee(),
                    promo_code=item.promo_code,
                    order=order,
                    vendor=item.vendor,
                )
            # Track promo code usage — derive discount from face value vs Order.total,
            # because our Stripe line item already has the discount baked in so
            # line_item.unit_amount == amount_total (face - charged == 0).
            from django.db.models import F as _F
            promo_codes_used = set(
                item.promo_code for item in items if item.promo_code
            )
            for code in promo_codes_used:
                try:
                    promo = PromoCode.objects.select_for_update().get(code=code)
                    already_recorded = PromoCodeUsage.objects.filter(
                        promo_code=promo,
                        order_id=str(order.id)
                    ).exists()
                    if not already_recorded:
                        # Face value = sum of ticket prices at full price
                        _face = sum(item.ticket.price * item.quantity for item in items)
                        _charged = stripe_total
                        _discount = max(Decimal('0.00'), _face - _charged)
                        PromoCodeUsage.objects.create(
                            promo_code=promo,
                            customer_email=customer.email,
                            order_id=str(order.id),
                            discount_amount=_discount,
                        )
                        PromoCode.objects.filter(pk=promo.pk).update(
                            current_uses=_F('current_uses') + 1
                        )
                        logger.info(f"Webhook: promo code '{code}' usage recorded for order {order.id}, discount={_discount}")
                except PromoCode.DoesNotExist:
                    logger.warning(f"Webhook: promo code '{code}' not found during usage tracking")

            cart.delete()

        logger.info(
            f"Webhook: recovered order {order.id} for session {session_id}, customer={customer_email}"
        )

        # Update Stripe PaymentIntent description with Order # (same as success URL handler)
        try:
            from order.stripe_utils import build_stripe_description, build_stripe_metadata_from_order
            import stripe as _stripe
            _stripe.api_key = settings.STRIPE_SECRET_KEY
            first_item = order.orderitem_set.first()
            if first_item:
                _desc = build_stripe_description(
                    first_item.event_ticket.event.name,
                    first_item.event_ticket.name,
                    order_id=order.id,
                    customer_email=order.emailAddress,
                )
            else:
                _desc = f"{order.emailAddress} | Order #{order.id}"
            payment_intent_id = session.get('payment_intent', '')
            if payment_intent_id:
                _stripe.PaymentIntent.modify(
                    payment_intent_id,
                    description=_desc,
                    metadata=build_stripe_metadata_from_order(order),
                )
                logger.info(f"Webhook: updated Stripe description for order {order.id}: {_desc}")
        except Exception as e:
            logger.error(f"Webhook: failed to update Stripe description for order {order.id}: {e}")

        try:
            send_mail(order.id)
        except Exception as e:
            logger.error(f"Webhook: email failed for recovered order {order.id}: {e}")

    except Exception as e:
        logger.error(f"Webhook: failed to create order for session {session_id}: {e}", exc_info=True)
        raise  # re-raise so the webhook view returns 500 → Stripe retries


def _webhook_handle_refund(charge):
    """
    Called when Stripe fires charge.refunded.
    Handles refunds issued directly via Stripe dashboard (bypassing Eventlinez UI).
    Idempotent: skips if the order is already marked REFUNDED.
    """
    payment_intent_id = charge.get('payment_intent')
    if not payment_intent_id:
        logger.warning("charge.refunded webhook: no payment_intent on charge object")
        return

    try:
        order = Order.objects.get(payment_code=payment_intent_id)
    except Order.DoesNotExist:
        logger.warning(f"charge.refunded webhook: no order found for payment_intent {payment_intent_id}")
        return

    if order.status == Order.STATUS_REFUNDED:
        logger.info(f"charge.refunded webhook: order {order.id} already REFUNDED, skipping")
        return

    refunds_data = charge.get('refunds', {}).get('data', [])
    stripe_refund_id = refunds_data[0].get('id', '') if refunds_data else ''
    refund_amount = Decimal(str(charge.get('amount_refunded', 0))) / 100

    ticket_refund = None
    tickets_cancelled = 0

    with transaction.atomic():
        order_locked = Order.objects.select_for_update().get(pk=order.pk)
        if order_locked.status == Order.STATUS_REFUNDED:
            return  # lost the race, already handled

        tickets_to_cancel = list(
            Ticket.objects.filter(order_item__order=order_locked)
        )
        tickets_cancelled = len(tickets_to_cancel)

        CancelledTicket.objects.bulk_create([
            CancelledTicket(
                original_ticket_id=t.id,
                uuid=t.uuid,
                event_ticket=t.event_ticket,
                customer=t.customer,
                order_item=t.order_item,
                price=t.price,
                guest_name=t.guest_name,
                day_number=t.day_number,
                day_event=t.day_event,
                vendor=t.vendor,
                original_checkin_date=t.checkin_date,
                cancelled_reason=CancelledTicket.REASON_REFUNDED,
            )
            for t in tickets_to_cancel
        ], ignore_conflicts=True)
        Ticket.objects.filter(order_item__order=order_locked).delete()

        order_locked.status = Order.STATUS_REFUNDED
        order_locked.save(update_fields=['status'])

        ticket_refund, _ = TicketRefund.objects.get_or_create(
            order=order_locked,
            defaults={
                'stripe_refund_id': stripe_refund_id,
                'amount': refund_amount,
                'reason': 'Refunded via Stripe dashboard (webhook)',
            }
        )

    logger.info(
        f"charge.refunded webhook: order {order.id} marked REFUNDED, "
        f"{tickets_cancelled} ticket(s) invalidated, stripe_refund={stripe_refund_id}"
    )

    try:
        order_locked.send_refund_notification(ticket_refund)
    except Exception as e:
        logger.error(f"charge.refunded webhook: refund email failed for order {order.id}: {e}")


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
    session_id = request.GET.get('session_id')
    if not session_id:
        return render(request, 'order/error.html', {
            'error': 'No payment session ID provided.',
            'PROD': settings.PROD,
        })

    # ── Idempotency: if order already exists for this session, go straight to thanks ──
    existing = Order.objects.filter(token=session_id).first()
    if existing:
        logger.info(f"Order {existing.id} already exists for session {session_id}, redirecting to thanks")
        return redirect('order:thanks', existing.id)

    # ── Retrieve and validate the Stripe session ──
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.InvalidRequestError as e:
        logger.error(f"Invalid Stripe session {session_id}: {e}")
        return render(request, 'order/error.html', {
            'error': 'Invalid payment session. Please contact support if you were charged.',
            'PROD': settings.PROD,
        })
    except Exception as e:
        logger.error(f"Failed to retrieve Stripe session {session_id}: {e}")
        return render(request, 'order/error.html', {
            'error': 'Could not verify payment. Please contact support if you were charged.',
            'PROD': settings.PROD,
        })

    if session.payment_status != 'paid':
        logger.warning(f"Session {session_id} not paid (status={session.payment_status})")
        return render(request, 'order/error.html', {
            'error': f'Payment not completed (status: {session.payment_status}). You have not been charged.',
            'PROD': settings.PROD,
        })

    # ── Look up the cart using the ID Stripe stored — NOT the session cookie ──
    # client_reference_id = cart.id (DB pk) set during checkout session creation.
    # This works even if the user's session cookie is gone (closed tab, network drop).
    cart_pk = session.client_reference_id
    try:
        cart = Cart.objects.get(id=cart_pk)
    except (Cart.DoesNotExist, ValueError, TypeError):
        logger.error(
            f"Cart pk={cart_pk} not found for paid session {session_id} "
            f"(payment_intent={session.payment_intent}) — webhook recovery will handle it"
        )
        return render(request, 'order/error.html', {
            'error': (
                'Your payment was successful but we could not locate your cart. '
                'Your tickets will be confirmed shortly via email — '
                'please do not pay again. Contact support if you do not receive them.'
            ),
            'PROD': settings.PROD,
        })

    # ── Customer profile ──
    try:
        customer = request.user.customer
    except Exception:
        logger.error(f"User {request.user.id} has no customer profile for session {session_id}")
        return render(request, 'order/error.html', {
            'error': 'Customer profile not found. Please complete your profile and contact support.',
            'PROD': settings.PROD,
        })

    items = cart.cartitem_set.filter(active=True)
    if not items.exists():
        # Cart items were cleared — most likely the 5-minute reservation timer fired
        # in a background tab while the customer was on the Stripe payment page.
        # Payment already succeeded, so log it and let the webhook recover the order.
        logger.error(
            f"Cart {cart.id} has no active items for paid session {session_id} "
            f"(payment_intent={session.payment_intent}) — timer likely cleared items; "
            f"webhook recovery will create the order"
        )
        return render(request, 'order/error.html', {
            'error': (
                'Your payment was received successfully. '
                'Your tickets are being confirmed — you will receive a confirmation email shortly. '
                'Please do not pay again.'
            ),
            'PROD': settings.PROD,
        })

    # ── Create order + items atomically ──
    stripe_total = Decimal(str(session.amount_total or 0)) / 100
    try:
        with transaction.atomic():
            order = Order.objects.create(
                total=stripe_total,
                emailAddress=customer.email,
                customer=customer,
                token=session_id,
                payment_code=session.payment_intent,
            )
            for item in items:
                OrderItem.objects.create(
                    event_ticket=item.ticket,
                    quantity=item.quantity,
                    unit_price=item.ticket.price,
                    amount=item.price_total(),
                    fee=item.fee(),
                    promo_code=item.promo_code,
                    order=order,
                    vendor=item.vendor,
                )
            # Track promo code usage
            from django.db.models import F
            promo_codes_used = set(item.promo_code for item in items if item.promo_code)
            for code in promo_codes_used:
                try:
                    promo = PromoCode.objects.select_for_update().get(code=code)
                    if not PromoCodeUsage.objects.filter(promo_code=promo, order_id=str(order.id)).exists():
                        PromoCodeUsage.objects.create(
                            promo_code=promo,
                            customer_email=customer.email,
                            order_id=str(order.id),
                            discount_amount=cart.promo_discount or 0,
                        )
                        PromoCode.objects.filter(pk=promo.pk).update(current_uses=F('current_uses') + 1)
                except PromoCode.DoesNotExist:
                    logger.warning(f"Promo code '{code}' not found during usage tracking")

            cart.delete()

    except Exception as e:
        logger.error(f"Order creation failed for session {session_id}: {e}", exc_info=True)
        return render(request, 'order/error.html', {
            'error': (
                'Your payment was received but we encountered an error saving your order. '
                'Please do not pay again — contact support with your email address and we will sort it out.'
            ),
            'PROD': settings.PROD,
        })

    # Clear the pending session guard so future purchases for a new cart work normally
    request.session.pop(f'pending_stripe_session_{cart_pk}', None)

    # ── Update Stripe description + metadata with Order # and customer email ──
    try:
        from order.stripe_utils import build_stripe_description, build_stripe_metadata_from_order
        first_item = order.orderitem_set.first()
        if first_item:
            description = build_stripe_description(
                first_item.event_ticket.event.name,
                first_item.event_ticket.name,
                order_id=order.id,
                customer_email=order.emailAddress,
            )
        else:
            description = f"{order.emailAddress} | Order #{order.id}"
        stripe.PaymentIntent.modify(
            session.payment_intent,
            metadata=build_stripe_metadata_from_order(order),
            description=description,
        )
        logger.info(f"Updated Stripe description for order {order.id}: {description}")
    except Exception as e:
        logger.error(f"Failed to update Stripe description for order {order.id}: {e}")

    try:
        send_mail(order.id)
    except Exception as e:
        logger.error(f"Confirmation email failed for order {order.id}: {e}")

    logger.info(f"Order {order.id} created via success URL for session {session_id}")
    return redirect('order:thanks', order.id)
