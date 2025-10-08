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
from promoter.models import Vendor
from .models import Cart, CartItem
from .utils import track_cart_abandonment, mark_cart_converted
from django.conf import settings

from django.contrib import messages 

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
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    data = json.loads(request.body)
    promocode = data.get("promo_code")
    vendor_code = data.get("vendor_code")

    vendor = None
    if vendor_code:
        vendor = Vendor.objects.get(code=vendor_code)

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
            CartItem.objects.create(ticket=ticket,
                                    cart=cart,
                                    quantity=quantity,
                                    promo_code=promocode,
                                    vendor=vendor)
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
        return render(request, 'cart.html', dict(total=total, cart_items=items, PROD=settings.PROD))
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
        
        all_items = CartItem.objects.filter(cart=cart, active=True)
        sold_out_items = all_items.filter(ticket__sold_out=True)

        if sold_out_items.exists():
            sold_out_names = [item.ticket.name for item in sold_out_items]
            messages.warning(request, "The following items are no longer available: " + ", ".join(sold_out_names))
        
        cart_items = all_items.exclude(ticket__sold_out=True)

        promo_code = cart_items.first().promo_code if cart_items.exists() else None
        total = sum(item.price_total() for item in cart_items)

    except Cart.DoesNotExist:
        logger.error("The cart does not exist.")
        cart_items = []
        promo_code = None
        total = 0

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

    return render(request, 'cart.html', dict(total=total, cart_items=cart_items, promo_code=promo_code, PROD=settings.PROD))


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

    invalid_items = items.filter(ticket__sold_out=True)
    if invalid_items.exists():
        names = [item.ticket.name for item in invalid_items]
        messages.error(request, "The following tickets are sold out: " + ", ".join(names))
        return redirect('cart:cart_detail') 

    # Check if Stripe is properly configured with real keys
    if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY in ['sk_test_51234567890abcdef', 'sk_live_51H1234567890abcdef']:
        return JsonResponse({
            'error': 'Payment processing is not available. Please contact administrator for checkout assistance.'
        }, status=500)
    
    stripe.api_key = settings.STRIPE_SECRET_KEY
    line_items = []

    # https://stripe.com/docs/billing/subscriptions/decimal-amounts
    cents = 100

    try:
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
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return JsonResponse({
            'error': f'Payment processing error: {str(e)}'
        }, status=500)

    try:
        # Build description and metadata for Stripe payment using helper functions
        from order.stripe_utils import build_stripe_description, build_stripe_metadata_from_cart
        
        first_item = items.first()
        if first_item:
            event_name = first_item.ticket.event.name
            tier_name = first_item.ticket.name
            description = build_stripe_description(event_name, tier_name, cart_id=cart.id)
        else:
            description = f"Event Tickets (Cart #{cart.id})"
        
        # Build comprehensive metadata
        metadata = build_stripe_metadata_from_cart(
            cart=cart,
            customer_email=request.user.username
        )
        
        server = request.get_raw_uri().replace(request.get_full_path(), "")
        session = stripe.checkout.Session.create(
            payment_intent_data={
                'setup_future_usage': 'off_session',
                'description': description,
                'metadata': metadata,
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
    except stripe.error.StripeError as e:
        logger.error(f"Stripe session creation error: {e}")
        return JsonResponse({
            'error': f'Payment session creation failed: {str(e)}'
        }, status=500)

    # Mark cart as about to be converted (we'll mark as fully converted in order processing)
    try:
        mark_cart_converted(cart.cart_id, order_id=session.id)
    except Exception as e:
        logger.warning(f"Failed to mark cart as converted: {e}")

    return JsonResponse({
        'session_id': session.id,
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY
    })
