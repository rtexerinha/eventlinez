from django.urls import path

from ticket.views import ticket_qrcode, generate_pdf_reportlab, search_checkin

urlpatterns = [
    path('qrcode/', ticket_qrcode, name='ticket_qrcode'),
    path('search', search_checkin, name='search_guest'),
    path('pdf/', generate_pdf_reportlab, name='pdf'),
]
