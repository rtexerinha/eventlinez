from .models import Cart, CartItem
from .views import _cart_id


def counter(request):
	item_count = 0
	if 'admin' in request.path:
		return {}
	else:
		try:
			# Check if request has session attribute and handle gracefully
			if not hasattr(request, 'session'):
				return dict(item_count=0)
				
			cart = Cart.objects.filter(cart_id=_cart_id(request))
			cart_items = CartItem.objects.filter(
                cart=cart[:1],
                active=True,
                ticket__sold_out=False 
            )
			for cart_item in cart_items:
				item_count += cart_item.quantity
		except (Cart.DoesNotExist, AttributeError):
			item_count = 0
		except Exception:
			# Catch any other session-related errors to prevent sidebar failure
			item_count = 0
	return dict(item_count=item_count)
