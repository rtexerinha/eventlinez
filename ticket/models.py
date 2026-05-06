import uuid
from io import BytesIO

import qrcode
import qrcode.image.svg
import qrcode.image.svg
from django.core.validators import MinValueValidator
from django.db import models

from django.utils.safestring import mark_safe
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from customer.models import Customer
from eventlinez import settings
from django.utils import timezone


class Ticket(models.Model):
    event_ticket = models.ForeignKey('event.Ticket', on_delete=models.RESTRICT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    order_item = models.ForeignKey('order.OrderItem', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    guest_name = models.CharField(max_length=161, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    checkin_date = models.DateTimeField(blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    vendor = models.ForeignKey("promoter.Vendor", blank=True, null=True, on_delete=models.SET_NULL)
    day_number = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='For multi-day passes: which day this ticket is valid for (1, 2, 3...).'
    )
    day_event = models.ForeignKey(
        'event.Event',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='day_tickets',
        help_text='For multi-day passes: the specific event this day ticket is valid for.'
    )

    def as_qrcode(self):
        import re as _re
        host = settings.APP_HOST.rstrip('/')
        content = host + '/promoter/ticket/checkin/' + str(self.uuid) + '/'
        # SvgPathImage produces a viewBox-aware SVG; strip fixed mm dimensions so
        # CSS can scale it freely without the inline width/height overriding max-width.
        img = qrcode.make(content, image_factory=qrcode.image.svg.SvgPathImage, box_size=10)
        stream = BytesIO()
        img.save(stream)
        svg = stream.getvalue().decode()
        svg = _re.sub(r'\s+width="[^"]+"', '', svg)
        svg = _re.sub(r'\s+height="[^"]+"', '', svg)
        return mark_safe(svg)

    def _qrcode_reportlab(self):
        content = settings.APP_HOST.rstrip('/') + '/promoter/ticket/checkin/' + str(self.uuid) + '/'
        qr_code = qr.QrCodeWidget(content)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        c = Drawing(45, 45, transform=[200. / width, 0, 0, 200. / height, 0, 0])
        c.add(qr_code)
        return c

    def as_pdf(self):
        qrcodec = self._qrcode_reportlab()
        out = BytesIO()

        font_name = 'Helvetica'
        font_size = 10

        p = canvas.Canvas(out)
        p.setFont(font_name, font_size)
        p.setFillColor(HexColor('#565454'))

        p.setStrokeGray(0.8)
        p.rect(130, 780, 0, 0, fill=1)
        p.roundRect(130, 390, 300, 430, 10, stroke=1, fill=0)

        img_file = 'static/img/Eventlinez.png'
        p.drawImage(img_file, 230, 785, width=100, preserveAspectRatio=True, mask='auto')
        p.setStrokeGray(0.8)
        p.line(130, 780, 430, 780)
        p.setStrokeGray(0.6)

        if self.guest_name is None:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(150, 755, str(self.customer))
        else:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(150, 755, str(self.guest_name))
        p.drawString(380, 755, str(self.id))

        display_event = self.day_event if self.day_event else self.event_ticket.event
        month = timezone.localtime(display_event.event_date).strftime("%B %Y")
        day = timezone.localtime(display_event.event_date).strftime("%d")
        hour = timezone.localtime(display_event.event_date).strftime("%H:%M")

        location = display_event.address + ', ' + \
                   display_event.city.name + ', ' + \
                   display_event.city.state.name

        p.setFont("Helvetica-Bold", 18)
        p.setFillColor(HexColor('#FF0054'))
        p.drawString(270, 540, day)

        p.setFont("Helvetica", 12)
        p.setFillColor(HexColor('#565454'))
        p.drawString(270, 520, month)

        p.setFont("Helvetica", 10)
        p.drawString(270, 500, hour)

        p.setLineWidth(0.01)
        p.line(130, 480, 430, 480)

        p.setFont("Helvetica-Bold", 14)
        p.drawString(150, 450, str(self.event_ticket.event.name))

        p.setFont("Helvetica", 10)
        p.drawString(150, 430, str(self.event_ticket.name))

        if self.day_number:
            p.setFont("Helvetica-Bold", 10)
            p.setFillColor(HexColor('#d90075'))
            p.drawString(150, 415, 'Day %d of %d' % (self.day_number, self.event_ticket.days))
            p.setFillColor(HexColor('#565454'))
            p.setFont("Helvetica", 10)
            p.drawString(150, 400, location)
        else:
            p.setFont("Helvetica", 10)
            p.drawString(150, 410, location)

        renderPDF.draw(qrcodec, p, 180, 550)
        p.showPage()
        p.save()
        pdf = out.getvalue()
        out.close()

        return pdf

    def __str__(self):
        if self.day_number:
            return "%s/%s/Day %s" % (self.event_ticket.event.name, self.event_ticket.name, self.day_number)
        return "%s/%s" % (self.event_ticket.event.name, self.event_ticket.name)
