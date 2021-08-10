from django.urls import path

from ticket.views import ticket_qrcode, generate_pdf_reportlab

urlpatterns = [
    path('qrcode/', ticket_qrcode, name='ticket_qrcode'),
    path('pdf/', generate_pdf_reportlab, name='pdf'),
]
