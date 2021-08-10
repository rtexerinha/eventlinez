import uuid
from io import BytesIO

import qrcode
import qrcode.image.svg
import qrcode.image.svg
from django.core.validators import MinValueValidator
from django.db import models

from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.pdfgen import canvas
from weasyprint import CSS, HTML

from customer.models import Customer
from event.models import Event
from eventlinez import settings


class Ticket(models.Model):
    event_ticket = models.ForeignKey('event.Ticket', on_delete=models.RESTRICT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    order_item = models.ForeignKey('order.OrderItem', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    guest_name = models.CharField(max_length=161, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    checkin_date = models.DateTimeField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    def as_qrcode(self):
        # content = host + '/qrcode/?tkt=' + str(self.uuid)
        host = settings.APP_HOST
        content = host + '/promoter/ticket/checkin/' + str(self.uuid)
        img = qrcode.make(content, image_factory=qrcode.image.svg.SvgImage, box_size=20)
        stream = BytesIO()
        img.save(stream)
        svg = mark_safe(stream.getvalue().decode())
        return svg

    def as_qrcode_reportlab(self):
        content = settings.APP_HOST + '/promoter/ticket/checkin/' + str(self.uuid)
        qr_code = qr.QrCodeWidget(content)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        c = Drawing(45, 45, transform=[200. / width, 0, 0, 200. / height, 0, 0])
        c.add(qr_code)
        return c

    def as_pdf(self):
        host = settings.APP_HOST
        svg = self.as_qrcode()
        out = BytesIO()
        html_str = render_to_string("ticket/ticket_qrcode.html", {'svg': svg, 'ticket': self})
        html = HTML(string=html_str)
        html.write_pdf(out, stylesheets=[CSS(host + settings.STATIC_URL + 'css/ticket.css')],
                       presentational_hints=True)
        pdf = out.getvalue()
        out.close()
        return pdf

    def as_pdf_report(self):
        qrcodec = self.as_qrcode_reportlab()
        out = BytesIO()
        # response = HttpResponse(content_type='application/pdf')
        # response['Content-Disposition'] = 'attachment; filename="file.pdf"'
        p = canvas.Canvas(out)

        p.line(30, 820, 560, 820)
        p.line(30, 560, 560, 560)
        p.line(30, 560, 30, 820)
        p.line(560, 560, 560, 820)

        if self.guest_name is None:
            p.drawString(50, 760, str(self.customer))
        else:
            p.drawString(50, 760, str(self.guest_name))
        p.drawString(250, 760, str(self.id))
        p.drawString(50, 720, str(self.event_ticket.event.event_date.strftime("%d %B %Y %H:%M")))
        p.drawString(50, 700, str(self.event_ticket.event.address) + ', ' + str(self.event_ticket.event.city)
                     + ', ' + str(self.event_ticket.event.city.state))
        p.drawString(50, 680, str(self.event_ticket.event.name))

        renderPDF.draw(qrcodec, p, 320, 600)
        p.showPage()
        p.save()
        pdf = out.getvalue()
        out.close()
        return pdf

    def __str__(self):
        return "%s/%s" % (self.event_ticket.event.name, self.event_ticket.name)
