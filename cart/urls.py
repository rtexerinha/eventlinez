from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
	path('', views.cart_detail, name='detail'),
	path('add/', views.cart_add, name='add_cart'),
	path('checkout/', views.checkout, name='checkout'),
	path('stripe-cancel/', views.stripe_cancel, name='stripe-cancel'),
	path('expire/', views.expire_cart, name='expire'),
	path('<int:item_id>/<str:operation>/quantity/', views.change_quantity, name='change-quantity'),
	path('remove/item/<int:item_id>/', views.remove_item, name='remove-item'),
	path('apply-promo/', views.apply_promo_code, name='apply-promo'),
	path('remove-promo/', views.remove_promo_code, name='remove-promo'),
]
