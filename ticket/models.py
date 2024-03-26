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
from event.models import Event
from eventlinez import settings
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError


class Ticket(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, blank=True, null=True)
    order_item = models.ForeignKey('order.OrderItem', on_delete=models.PROTECT, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], blank=True,
                                null=True)
    vendor = models.ForeignKey("promoter.Vendor", blank=True, null=True, on_delete=models.SET_NULL)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    event_ticket = models.ForeignKey('event.Ticket', on_delete=models.RESTRICT)
    guest_name = models.CharField(max_length=161, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    checkin_date = models.DateTimeField(blank=True, null=True)
    isFree = models.BooleanField(default=False)
    email = models.EmailField(blank=False, null=False, default='')
    account_required = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)

    def clean(self):
        if self.isFree is False and self.customer is None:
            raise ValidationError({'customer': 'Customer is required'})

        if self.isFree is False and self.order_item is None:
            raise ValidationError({'Order': 'Order is required'})

        if self.isFree is False and self.price is None:
            raise ValidationError({'price': 'price is required'})

    def __str__(self):
        return "%s/%s" % (self.event_ticket.event.name, self.event_ticket.name)

    def as_qrcode(self):
        # content = host + '/qrcode/?tkt=' + str(self.uuid)
        host = settings.APP_HOST
        content = host + '/promoter/ticket/checkin/' + str(self.uuid)
        img = qrcode.make(content, image_factory=qrcode.image.svg.SvgImage, box_size=20)
        stream = BytesIO()
        img.save(stream)
        svg = mark_safe(stream.getvalue().decode())
        return svg

    def _qrcode_reportlab(self):
        content = settings.APP_HOST + '/promoter/ticket/checkin/' + str(self.uuid)
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

        month = timezone.localtime(self.event_ticket.event.event_date).strftime("%B %Y")
        day = timezone.localtime(self.event_ticket.event.event_date).strftime("%d")
        hour = timezone.localtime(self.event_ticket.event.event_date).strftime("%H:%M")

        location = self.event_ticket.event.address + ', ' + \
                   self.event_ticket.event.city.name + ', ' + \
                   self.event_ticket.event.city.state.name

        p.setFont("Helvetica-Bold", 18)
        p.setFillColor(HexColor('#FF0054'))
        p.drawString(270, 540, day)

        p.setFont("Helvetica", 12)
        p.setFillColor(HexColor('#565454'))
        p.drawString(250, 520, month)

        p.setFont("Helvetica", 10)
        p.drawString(270, 500, hour)

        p.setLineWidth(0.01)
        p.line(130, 480, 430, 480)

        p.setFont("Helvetica-Bold", 14)
        p.drawString(150, 450, str(self.event_ticket.event.name))

        p.setFont("Helvetica", 10)
        p.drawString(150, 430, str(self.event_ticket.name))

        p.setFont("Helvetica", 10)
        p.drawString(150, 410, location)

        renderPDF.draw(qrcodec, p, 180, 550)
        p.showPage()
        p.save()
        pdf = out.getvalue()
        out.close()

        return pdf

    def send_email(self):
        try:
            user = User.objects.get(username=self.email).first_name
        except User.DoesNotExist:
            user = self.guest_name

        if self.account_required and user == self.guest_name:
            subject = "Eventlinez - Create Account Required"
            message_template = 'freeticket/email/create-account-email.html'
            output_pdf = None
        else:
            subject = "Eventlinez - Free Ticket"
            message_template = 'freeticket/email/freeticket-email.html'
            output_pdf = self.as_pdf()

        message = render_to_string(message_template, {'freeticket': self, 'user': user})

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email='noreply@eventlinez.com',
            to=[self.email],
        )
        email.content_subtype = "html"

        if output_pdf:
            email.attach('ticket_{}.pdf'.format(self.id), output_pdf, 'application/pdf')

        try:
            email.send()
            self.is_email_sent = True
        except Exception:
            self.is_email_sent = False
        self.save()


@receiver(post_save, sender=Ticket)
def freeticket_email(sender, instance, **kwargs):
    if kwargs.get('created', False):
        instance.send_email()
