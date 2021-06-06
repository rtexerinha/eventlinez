from django.urls import path

from . import views

app_name = 'order'

urlpatterns = [
	path('thanks/<int:order_id>/', views.thanks, name='thanks'),
	path('history/', views.order_list, name='order_history'),
	path('<int:order_id>/', views.order_detail, name='order_detail'),
	path('success/', views.create, name='create_order'),
]
