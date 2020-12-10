import logging
from decimal import Decimal

import stripe
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from local_settings import EVENTLINEZ_FEE
from order.models import Order, OrderItem
from order.tasks import send_mail
from event.models import Event
from .models import Cart, CartItem
from .forms import AddItemToCardForm

logger = logging.getLogger(__name__)


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def cart_add(request, event_id):
    # TODO : Entender melhor a real utilidade do try/except e otimizar ainda mais essa view
    event = Event.objects.get(id=event_id)
    form = AddItemToCardForm(request.POST)
    promo_code = None

    if form.is_valid():
        promo_code = form.cleaned_data.get("promo_code")
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()
    try:
        cart_item = CartItem.objects.get(event=event, cart=cart)
        if cart_item.quantity < cart_item.event.stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(event=event,
                                            quantity=1,
                                            cart=cart,
                                            promo_code=promo_code)
        cart_item.save()
    return redirect('cart:cart_detail')


@login_required
def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (((cart_item.event.unit_price * Decimal(EVENTLINEZ_FEE)) +
                       cart_item.event.unit_price) * cart_item.quantity)
            counter += cart_item.quantity
    except Cart.DoesNotExist:
        logger.error("The cart doest not exist.")
        pass

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = int(total * 100)
    description = 'New Order'
    data_key = settings.STRIPE_PUBLISHABLE_KEY
    if request.method == 'POST':
        token = request.POST['stripeToken']
        email = request.POST['stripeEmail']
        billing_name = request.POST['stripeBillingName']
        billing_address1 = request.POST['stripeBillingAddressLine1']
        billingcity = request.POST['stripeBillingAddressCity']
        billing_postcode = request.POST['stripeBillingAddressZip']
        billing_country = request.POST['stripeBillingAddressCountryCode']
        shipping_name = request.POST['stripeShippingName']
        shipping_address1 = request.POST['stripeShippingAddressLine1']
        shippingcity = request.POST['stripeShippingAddressCity']
        shipping_postcode = request.POST['stripeShippingAddressZip']
        shipping_country = request.POST['stripeShippingAddressCountryCode']
        # promoter = request.POST['promoter']
        try:
            customer = stripe.Customer.create(email=email, source=token)
            logger.info("create customer")
            charge = stripe.Charge.create(
                amount=stripe_total,
                currency="usd",
                description=description,
                customer=customer.id
            )
        except stripe.error.CardError as err:
            # return HttpResponse(status=400, content=err.user_message)
            content = err.user_message
            return render(request, 'order/error_cart.html', {'content': content})
        logger.info("Creating the order")
        try:
            order = Order.objects.create(
                token=token,
                payment_code=charge.stripe_id,
                total=total,
                emailAddress=email,
                billingName=billing_name,
                billingAddress1=billing_address1,
                billingCity=billingcity,
                billingPostcode=billing_postcode,
                billingCountry=billing_country,
                shippingName=shipping_name,
                shippingAddress1=shipping_address1,
                shippingCity=shippingcity,
                shippingPostcode=shipping_postcode,
                shippingCountry=shipping_country,
                # promoter=promoter
            )
            for order_item in cart_items:
                oi = OrderItem(
                    event=order_item.event,
                    quantity=order_item.quantity,
                    price=order_item.event.unit_price,
                    promo_code=order_item.promo_code,
                    order=order,
                    # promoter=order_item.event.promoter
                )
                oi.save()
                event = Event.objects.get(id=order_item.event.id)
                event.stock = int(order_item.event.stock - order_item.quantity)
                event.save()
                order_item.delete()
                logger.info("The order has been created")
            send_mail.delay(order.id)
            return redirect('order:thanks', order.id)
        except ObjectDoesNotExist:
            return HttpResponse(status=400, content="Page errada")
    return render(request, 'cart.html', dict(cart_items=cart_items,
                                             total=total, counter=counter,
                                             data_key=data_key,
                                             stripe_total=stripe_total,
                                             description=description))


def cart_remove(request, event_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    event = get_object_or_404(Event, id=event_id)
    cart_item = CartItem.objects.get(event=event, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart:cart_detail')


def full_remove(request, event_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    event = get_object_or_404(Event, id=event_id)
    cart_item = CartItem.objects.get(event=event, cart=cart)
    cart_item.delete()
    return redirect('cart:cart_detail')
