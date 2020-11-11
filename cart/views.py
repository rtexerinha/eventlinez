import stripe
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMessage

from order.models import Order, OrderItem
from event.models import Event
from .models import Cart, CartItem

import logging

logger = logging.getLogger(__name__)


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    event = Event.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        cart.save()
    try:
        cart_item = CartItem.objects.get(event=event, cart=cart)
        if cart_item.quantity < cart_item.event.stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(event=event, quantity=1, cart=cart)
        cart_item.save()
    return redirect('cart:cart_detail')


def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.event.unit_price * cart_item.quantity)
            counter += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = int(total * 100)
    description = 'New Order'
    data_key = settings.STRIPE_PUBLISHABLE_KEY
    if request.method == 'POST':
        try:
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
            customer = stripe.Customer.create(email=email, source=token)
            charge = stripe.Charge.create(
                amount=stripe_total,
                currency="usd",
                description=description,
                customer=customer.id
            )
            logger.info("Creating the order")
            try:
                order = Order.objects.create(
                    token=token,
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
                    shippingCountry=shipping_country
                )
                for order_item in cart_items:
                    oi = OrderItem(
                        event=order_item.event.name,
                        quantity=order_item.quantity,
                        price=order_item.event.unit_price,
                        order=order
                    )
                    oi.save()
                    event = Event.objects.get(id=order_item.event.id)
                    event.stock = int(order_item.event.stock - order_item.quantity)
                    event.save()
                    order_item.delete()
                    logger.info("The order has been created")
                return redirect('order:thanks', order.id)
            except ObjectDoesNotExist:
                pass
        except stripe.error.CardError as e:
            return False, e
    return render(request, 'cart.html', dict(cart_items=cart_items, total=total, counter=counter,
                                             data_key=data_key, stripe_total=stripe_total, description=description))


def cart_remove(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    event = get_object_or_404(Event, id=product_id)
    cart_item = CartItem.objects.get(event=event, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart:cart_detail')


def full_remove(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    event = get_object_or_404(Event, id=product_id)
    cart_item = CartItem.objects.get(event=event, cart=cart)
    cart_item.delete()
    return redirect('cart:cart_detail')


def send_email(order_id):
    transaction = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=transaction)
    try:
        '''Sending the order'''
        subject = "Eventlinez - New Order #{}".format(transaction.id)
        to = ['{}'.format(transaction.emailAddress)]
        from_email = "contact@calisamba.com"
        order_information = {
            'transaction': transaction,
            'order_items': order_items
        }
        message = get_template('email/email.html').render(order_information)
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        msg.send()
    except IOError as e:
        return e
