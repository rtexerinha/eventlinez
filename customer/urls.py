from django.urls import path

from customer.views import signup_view, signin_view, signout_view

urlpatterns = [
    path('account/create/', signup_view, name='signup'),
    path('account/login/', signin_view, name='signin'),
    path('account/logout/', signout_view, name='signout'),
]
