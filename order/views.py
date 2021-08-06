import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect

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
    return render(request, 'thanks.html', {'customer_order': customer_order, 'tickets': tickets})


@login_required()
def order_list(request):
    email = str(request.user.username)
    orders = Order.objects.filter(emailAddress=email)
    return render(request, 'order/orders_list.html', {'orders': orders})


@login_required()
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'order/order_detail.html', {'order': order})


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
            order=order
        )
    cart.delete()
    send_mail(order.id)
    return redirect('order:thanks', order.id)
