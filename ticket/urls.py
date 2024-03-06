from django.urls import path

from ticket.views import ticket_qrcode, search_checkin, search_ticket_sold
from .api import TicketSoldListAPIView, TicketSoldCheckinAPIView, TicketSoldCheckinQrcodeAPIView, \
    TicketSoldDetailsAPIView, FreeTicketAPIView, FreeTicketListAPIView, FreeTicketDetailsAPIView, \
    send_email_api_view

urlpatterns = [
    path('qrcode/', ticket_qrcode, name='ticket_qrcode'),
    path('search', search_checkin, name='search_guest'),
    path('search/ticket/sold/', search_ticket_sold, name='search_ticket_sold'),

    # APIs de ticketSold
    path('api/search', TicketSoldListAPIView.as_view(), name='api_search_guest'),
    path('api/checkin/<int:pk>', TicketSoldCheckinAPIView.as_view(),
         name='api_checkin_guest'),
    path('api/checkin/qrcode/<uuid:uuid>', TicketSoldCheckinQrcodeAPIView.as_view(),
         name='api_checkin_qrcode'),
    path('api/search/<int:pk>', TicketSoldDetailsAPIView.as_view(),
         name='api_search_id'),

    # API FREE TICKET
    path('api/free/new', FreeTicketAPIView.as_view()),
    path('api/free/list', FreeTicketListAPIView.as_view(), name='api_list_freeticket'),
    path('api/free/list/<int:pk>', FreeTicketDetailsAPIView.as_view(),
         name='api_free_ticket_per_id'),
    path('api/free/<int:pk>/resend/email', send_email_api_view,
         name='api_free_ticket_per_id'),
]
