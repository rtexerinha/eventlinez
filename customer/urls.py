from django.urls import path

from customer.views import signup_view, signout_view

urlpatterns = [
    path('account/create/', signup_view, name='signup'),
    path('account/logout/', signout_view, name='signout'),
]
