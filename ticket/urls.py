from django.urls import path

from ticket.views import ticket_qrcode, search_checkin, search_ticket_sold
from .api import TicketListAPIView, TicketCheckinAPIView
urlpatterns = [
    path('qrcode/', ticket_qrcode, name='ticket_qrcode'),
    path('search', search_checkin, name='search_guest'),
    path('search/ticket/sold/', search_ticket_sold, name='search_ticket_sold'),
    path('api/search', TicketListAPIView.as_view(), name='api_search_guest'),
    path('api/checkin/<int:pk>', TicketCheckinAPIView.as_view(),
         name='api_checkin_guest'),
]
