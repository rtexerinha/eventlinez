from django.urls import path

from ticket.views import ticket_qrcode


urlpatterns = [
    path('qrcode/', ticket_qrcode, name='ticket_qrcode')
]
