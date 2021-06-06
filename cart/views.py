import logging
import stripe
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse
from event.models import Event
from .models import Cart, CartItem
from .forms import AddItemToCardForm
from django.views.decorators.csrf import csrf_exempt

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
        qtd_available = event.sales_info()['qtd_available']
        if cart_item.quantity >= qtd_available:
            raise Exception('Quantity cannot be greater than %s' % qtd_available)
        if cart_item.quantity < qtd_available:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(event=event, quantity=1,
                                cart=cart, promo_code=promo_code)
    return redirect('cart:cart_detail')


@login_required
def cart_detail(request, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        total = cart.amount()
    except Cart.DoesNotExist:
        logger.error("The cart doest not exist.")
        total = 0
        pass
    return render(request, 'cart.html', dict(total=total, cart_items=cart_items))


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


@login_required
@csrf_exempt
def checkout(request):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    cart_items = CartItem.objects.filter(cart=cart, active=True)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    line_items = []

    # https://stripe.com/docs/billing/subscriptions/decimal-amounts
    cents = 100

    for item in cart_items:
        product = stripe.Product.create(name=item.event.name)
        line_item = {
            'price_data': {
                'product': product.id,
                'unit_amount_decimal': item.price_total() * cents,
                'currency': 'usd'
            },
            'quantity': 1,
        }
        line_items.append(line_item)

    server = request.get_raw_uri().replace(request.get_full_path(), "")
    session = stripe.checkout.Session.create(
        mode='payment',
        payment_method_types=['card'],
        success_url=server + '/order/success/?session_id={CHECKOUT_SESSION_ID}"',
        cancel_url=server + '/cart/',
        line_items=line_items,
        customer_email=request.user.username,
    )

    return JsonResponse({
        'session_id': session.id,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY
    })
