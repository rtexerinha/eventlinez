import logging
import json

import stripe
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from event.models import Ticket
from .models import Cart, CartItem

logger = logging.getLogger(__name__)


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


@csrf_exempt
def cart_add(request):
    """
    Adiciona cria o carrinho e adiciona os tickets ao carrinho.
    """
    data = json.loads(request.body)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    promocode = data.get("promo_code")
    for tkt in data['tickets']:
        ticket = Ticket.objects.get(pk=tkt['id'])
        quantity = tkt['quantity']
        qtd_available = ticket.qty_available()

        if tkt['quantity'] == 0:
            continue
        if tkt['quantity'] > qtd_available:
            return JsonResponse({"message": 'Quantity cannot be greater than %s' % qtd_available}, status=400)
        if tkt['quantity'] < 0:
            return JsonResponse({"message": 'Quantity cannot be less than 0'}, status=400)
        item = cart.cartitem_set.filter(ticket=ticket).first()
        if item is not None and item.quantity != 0:
            item.quantity = item.quantity + quantity
            item.save()
        else:
            CartItem.objects.create(ticket=ticket, cart=cart, quantity=quantity, promo_code=promocode)
    return JsonResponse({"status": "ok"}, status=201)


@login_required()
def change_quantity(request, item_id, operation):
    """
    Altera (incrementa ou decrementa) a quantidade de um item no carrinho.
    :param request
    :param item_id: Id da linha
    :param operation: Operaçãoque será realizada. Os valores possíveis são "increment" ou "decrement"
    :return:
    """
    cart = Cart.objects.get(cart_id=_cart_id(request))
    item = CartItem.objects.get(pk=item_id, cart=cart, active=True)

    if operation == "increment":
        item.quantity = item.quantity + 1
    elif operation == "decrement" and item.quantity == 1:
        total = cart.amount()
        items = cart.cartitem_set.all()
        return render(request, 'cart.html', dict(total=total, cart_items=items))
    elif operation == "decrement":
        item.quantity = item.quantity - 1
    else:
        return HttpResponse("Invalid cart iperation", status=400)
    item.save()
    return redirect('cart:detail')


@login_required
def cart_detail(request, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        item = cart_items.first()
        promo_code = None
        if item:
            promo_code = item.promo_code
        total = cart.amount()
    except Cart.DoesNotExist:
        logger.error("The cart doest not exist.")
        total = 0
        pass
    return render(request, 'cart.html', dict(total=total, cart_items=cart_items, promo_code=promo_code))


def remove_item(request, item_id):
    """
    Remove um item do carrinho
    :param request
    :param item_id: Id do item que será removido
    :return:
    """
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('cart:detail')


@login_required
@csrf_exempt
def checkout(request):
    """
    Faz o redirecionamento do carrinho para processo de checkout no Stripe
    """
    cart = Cart.objects.get(cart_id=_cart_id(request))
    items = CartItem.objects.filter(cart=cart, active=True)
    stripe.api_key = settings.STRIPE_SECRET_KEY
    line_items = []

    # https://stripe.com/docs/billing/subscriptions/decimal-amounts
    cents = 100

    for item in items:
        product = stripe.Product.create(name=str(item.ticket))
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
        payment_intent_data={
            'setup_future_usage': 'off_session',
        },
        mode='payment',
        payment_method_types=['card'],
        success_url=server + '/order/success/?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=server + '/cart/',
        line_items=line_items,
        customer_email=request.user.username,
        client_reference_id=cart.id,
        allow_promotion_codes=True
    )

    return JsonResponse({
        'session_id': session.id,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY
    })
