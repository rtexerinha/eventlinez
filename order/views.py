import stripe
import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from cart.models import Cart
from cart.views import _cart_id
from order.tasks import send_mail
from ticket.models import Ticket
from .models import Order
from .models import OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required()
def thanks(request, order_id):
    customer_order = None
    tickets = None
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
        tickets = Ticket.objects.filter(order_item__order=customer_order).order_by('created_at')
    return render(request, 'thanks.html', {'customer_order': customer_order, 'tickets': tickets, 'PROD': settings.PROD})


@login_required()
def order_list(request):
    email = str(request.user.username)
    orders = Order.objects.filter(emailAddress=email)
    return render(request, 'order/orders_list.html', {'orders': orders, 'PROD': settings.PROD})


@login_required()
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'order/order_detail.html', {'order': order, 'PROD': settings.PROD})


def create_order(session):
    order = Order.objects.filter(Token=session.id)
    if order:
        cart_id = session.client_reference_id
        cart = Cart.objects.get(cart_id=cart_id)

        order = Order.objects.create(
            total=cart.amount(),
            emailAddress=session.customer_details.email,
            customer='como conseguir esse customer',
            token=session.id,
            payment_code=session.payment_intent
        )
        return order
    return None


def fulfill_order(session, new_order):
    if new_order is None:
        return
    cart_id = session.client_reference_id
    cart = Cart.objects.get(cart_id=cart_id)

    items = cart.cartitem_set.filter(active=True)
    stripe.PaymentIntent.modify(
        session.payment_intent,
        metadata={"new_order_id": new_order.id},
        description="%s (New Order #%s)" % (str(items.first().ticket), new_order.id)
    )
    for item in items:
        OrderItem.objects.create(
            order=new_order,
            event_ticket=item.ticket,
            quantity=item.quantity,
            unit_price=item.ticket.price,
            amount=item.price_total(),
            fee=item.fee(),
            promo_code=item.promo_code,
            vendor=item.vendor
        )
    cart.delete()
    send_mail(new_order.id)


@login_required()
def create(request):
    cart_id = _cart_id(request)
    cart = Cart.objects.get(cart_id=cart_id)
    session_id = request.GET.get('session_id')
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status != "paid":
        raise Exception('Payment not made')
    if session.client_reference_id != str(cart.id):
        raise Exception('The payment session is invalid for this cart %d')

    order = Order.objects.create(
        total=cart.amount(),
        emailAddress=request.user.customer.email,
        customer=request.user.customer,
        token=session_id,
        payment_code=session.payment_intent
    )

    items = cart.cartitem_set.filter(active=True)
    stripe.PaymentIntent.modify(
        session.payment_intent,
        metadata={"order_id": order.id},
        description="%s (Order #%s)" % (str(items.first().ticket), order.id)
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
            vendor=item.vendor
        )
    cart.delete()
    send_mail(order.id)
    return redirect('order:thanks', order.id)


logger = logging.getLogger('order')


@csrf_exempt
def stripe_webhook(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    payload = request.body
    logger.info('payload', payload)
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    endpoint_secret = 'whsec_Vaq3YFZP8yku64xFhqR9qH0iunP5ZEUj'

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    logger.info('event', event)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order = create_order(session)

        if session.payment_status == "paid":
            if order is not None:
                fulfill_order(session)

    return JsonResponse({'status': 'success'})
