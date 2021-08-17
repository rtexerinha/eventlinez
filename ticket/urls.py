from django.urls import path

from ticket.views import ticket_qrcode, generate_pdf_reportlab, search_checkin, search_ticket_sold

urlpatterns = [
    path('qrcode/', ticket_qrcode, name='ticket_qrcode'),
    path('search', search_checkin, name='search_guest'),
    path('search/ticket/sold/', search_ticket_sold, name='search_ticket_sold'),
    path('pdf/', generate_pdf_reportlab, name='pdf'),
]
