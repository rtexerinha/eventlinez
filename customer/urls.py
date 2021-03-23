from django.urls import path

from customer.views import signup_view, signout_view, update_customer, reset_password_customer

urlpatterns = [
    path('account/create/', signup_view, name='signup'),
    path('account/logout/', signout_view, name='signout'),
    path('update/', update_customer, name='customer_update'),
    path('reset_password/', reset_password_customer, name='reset_password_costomer')
]
