from django.utils import timezone
from django.contrib.auth.models import User
from .models import Cart, CartItem, AbandonedCart, AbandonedCartItem


def track_cart_abandonment(cart_id, user=None, email=None):
    """
    Track cart abandonment for reminder emails
    """
    try:
        cart = Cart.objects.get(cart_id=cart_id)
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        
        if not cart_items.exists():
            return None
            
        # Get user information
        if user and user.is_authenticated:
            customer_email = email or getattr(user, 'email', '')
            customer_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip()
            if not customer_name:
                customer_name = user.username
        else:
            customer_email = email or ''
            customer_name = ''
            
        if not customer_email:
            return None
            
        # Calculate cart totals
        total_amount = sum(item.price_total() for item in cart_items)
        items_count = cart_items.count()
        
        # Create or update abandoned cart record
        abandoned_cart, created = AbandonedCart.objects.get_or_create(
            cart=cart,
            defaults={
                'user': user if user and user.is_authenticated else None,
                'email': customer_email,
                'customer_name': customer_name,
                'total_amount': total_amount,
                'items_count': items_count,
                'abandoned_at': timezone.now(),
            }
        )
        
        if not created:
            # Update existing record
            abandoned_cart.email = customer_email
            abandoned_cart.customer_name = customer_name
            abandoned_cart.total_amount = total_amount
            abandoned_cart.items_count = items_count
            abandoned_cart.abandoned_at = timezone.now()
            abandoned_cart.save()
        
        # Clear existing items and add current items
        abandoned_cart.items.all().delete()
        
        for item in cart_items:
            AbandonedCartItem.objects.create(
                abandoned_cart=abandoned_cart,
                ticket_name=item.ticket.name,
                event_name=item.ticket.event.name,
                event_date=item.ticket.event.event_date,
                quantity=item.quantity,
                unit_price=item.ticket.price,
                total_price=item.price_total()
            )
            
        return abandoned_cart
        
    except Cart.DoesNotExist:
        return None


def mark_cart_converted(cart_id, order_id=None):
    """
    Mark cart as converted when order is completed
    """
    try:
        cart = Cart.objects.get(cart_id=cart_id)
        if hasattr(cart, 'abandoned_cart'):
            cart.abandoned_cart.mark_converted(order_id=order_id)
            return True
    except Cart.DoesNotExist:
        pass
    return False


def get_eligible_carts_for_reminder():
    """
    Get all carts eligible for reminder emails (30+ minutes old, not sent)
    """
    return AbandonedCart.objects.filter(
        reminder_status='pending'
    ).filter(
        abandoned_at__lte=timezone.now() - timezone.timedelta(minutes=30)
    )


def cleanup_expired_carts():
    """
    Mark carts as expired if they're 24+ hours old
    """
    expired_threshold = timezone.now() - timezone.timedelta(hours=24)
    expired_carts = AbandonedCart.objects.filter(
        abandoned_at__lte=expired_threshold,
        reminder_status__in=['pending', 'sent']
    )
    
    count = expired_carts.count()
    expired_carts.update(reminder_status='expired')
    return count
