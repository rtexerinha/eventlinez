from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
	path('', views.cart_detail, name='cart_detail'),
	path('add/', views.cart_add, name='add_cart'),
	path('checkout/', views.checkout, name='checkout'),
	path('remove/<int:event_id>/', views.cart_remove, name='cart_remove'),
	path('full_remove/<int:event_id>/', views.full_remove, name='full_remove'),
]
