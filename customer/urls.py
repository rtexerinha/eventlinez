from django.urls import path

from customer.views import signup_view, signout_view, update_customer, \
                           change_password_customer, guest_list, edit_guest

urlpatterns = [
    path('account/create/', signup_view, name='signup'),
    path('account/logout/', signout_view, name='signout'),
    path('update/', update_customer, name='customer_update'),
    path('reset_password/', change_password_customer, name='reset_password_costomer'),
    path('ticket/', guest_list, name='guest_list'),
    path('ticket/save/', edit_guest, name='saveTicket')
]
