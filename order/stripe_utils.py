"""
Utility functions for Stripe payment integration and order processing.

This module provides helper functions to ensure consistent descriptions and metadata
are sent to Stripe for all payment transactions.
"""
import logging
from typing import Dict, Optional, Any
from decimal import Decimal

logger = logging.getLogger(__name__)


def build_stripe_description(
    event_name: str,
    tier_name: str,
    order_id: Optional[int] = None,
    cart_id: Optional[int] = None
) -> str:
    """
    Build a consistent Stripe payment description.
    
    Args:
        event_name: Name of the event
        tier_name: Name of the ticket tier
        order_id: Order ID (if available)
        cart_id: Cart ID (if order not yet created)
    
    Returns:
        Formatted description string for Stripe
    
    Examples:
        >>> build_stripe_description("Calisamba in San Diego 2025", "Tier 1", order_id=5142)
        'Calisamba in San Diego 2025/Tier 1 (Order #5142)'
        
        >>> build_stripe_description("Calisamba in San Diego 2025", "Tier 1", cart_id=123)
        'Calisamba in San Diego 2025/Tier 1 (Cart #123)'
    """
    base_description = f"{event_name}/{tier_name}"
    
    if order_id:
        return f"{base_description} (Order #{order_id})"
    elif cart_id:
        return f"{base_description} (Cart #{cart_id})"
    else:
        return base_description


def build_stripe_metadata_from_cart(
    cart,
    items,
    customer_email: Optional[str] = None,
    order_id: Optional[int] = None
) -> Dict[str, str]:
    """
    Build comprehensive Stripe metadata from cart items.
    
    Args:
        cart: Cart object containing items
        items: QuerySet of CartItem objects
        customer_email: Customer email address (optional)
        order_id: Order ID (optional, if order already created)
    
    Returns:
        Dictionary of metadata for Stripe (max 50 key-value pairs, each value max 500 chars)
    
    Note:
        Stripe has limits: max 50 key-value pairs, each value max 500 characters
        We include up to 5 items to stay within limits
    """
    first_item = items.first()
    
    metadata = {
        'cart_id': str(cart.id),
        'items_count': str(items.count()),
    }
    
    if customer_email:
        metadata['customer_email'] = customer_email
    
    if order_id:
        metadata['order_id'] = str(order_id)
    
    if first_item:
        metadata['event_name'] = str(first_item.ticket.event.name)[:500]  # Stripe limit
        metadata['tier_name'] = str(first_item.ticket.name)[:500]
    
    # Add individual item info (up to 5 items due to Stripe metadata limits)
    for idx, item in enumerate(items[:5]):
        metadata[f'item_{idx}_event'] = str(item.ticket.event.name)[:500]
        metadata[f'item_{idx}_tier'] = str(item.ticket.name)[:500]
        metadata[f'item_{idx}_qty'] = str(item.quantity)
        metadata[f'item_{idx}_price'] = f"{item.price_total():.2f}"
    
    return metadata


def build_stripe_metadata_from_order(order) -> Dict[str, str]:
    """
    Build comprehensive Stripe metadata from an order.
    
    Args:
        order: Order object
    
    Returns:
        Dictionary of metadata for Stripe
    """
    from order.models import OrderItem
    
    items = OrderItem.objects.filter(order=order)
    first_item = items.first()
    
    metadata = {
        'order_id': str(order.id),
        'customer_email': order.emailAddress,
        'items_count': str(items.count()),
        'total_amount': f"{order.total:.2f}",
    }
    
    if first_item:
        metadata['event_name'] = str(first_item.event_ticket.event.name)[:500]
        metadata['tier_name'] = str(first_item.event_ticket.name)[:500]
    
    # Add individual item info (up to 5 items)
    for idx, item in enumerate(items[:5]):
        metadata[f'item_{idx}_event'] = str(item.event_ticket.event.name)[:500]
        metadata[f'item_{idx}_tier'] = str(item.event_ticket.name)[:500]
        metadata[f'item_{idx}_qty'] = str(item.quantity)
        metadata[f'item_{idx}_price'] = f"{item.amount:.2f}"
    
    return metadata


def update_stripe_payment_intent(
    payment_intent_id: str,
    order_id: int,
    event_name: str,
    tier_name: str,
    metadata: Optional[Dict[str, str]] = None
) -> bool:
    """
    Update Stripe PaymentIntent with order information.
    
    Args:
        payment_intent_id: Stripe PaymentIntent ID
        order_id: Order ID
        event_name: Event name
        tier_name: Ticket tier name
        metadata: Additional metadata (optional)
    
    Returns:
        True if successful, False otherwise
    """
    import stripe
    from django.conf import settings
    
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        description = build_stripe_description(event_name, tier_name, order_id=order_id)
        
        update_data = {
            'description': description,
        }
        
        if metadata:
            update_data['metadata'] = metadata
        
        stripe.PaymentIntent.modify(payment_intent_id, **update_data)
        logger.info(f"Successfully updated PaymentIntent {payment_intent_id} with description: {description}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update Stripe PaymentIntent {payment_intent_id}: {e}")
        return False


def validate_stripe_description(description: str) -> bool:
    """
    Validate that a Stripe description contains required information.
    
    Args:
        description: Stripe payment description
    
    Returns:
        True if description is valid and contains order/event info
    """
    if not description or description.strip() == '':
        return False
    
    # Check if description contains either "Order #" or event name pattern
    has_order = 'Order #' in description
    has_event_info = '/' in description  # Event name/Tier pattern
    
    return has_order or has_event_info

