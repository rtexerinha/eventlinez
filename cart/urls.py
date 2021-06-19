from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
	path('', views.cart_detail, name='detail'),
	path('add/', views.cart_add, name='add_cart'),
	path('checkout/', views.checkout, name='checkout'),
	path('remove/item/<int:item_id>/', views.remove_item, name='remove-item'),
]
