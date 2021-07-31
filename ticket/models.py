import uuid
from io import BytesIO

import qrcode
import qrcode.image.svg
import qrcode.image.svg

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.safestring import mark_safe

from customer.models import Customer
from event.models import Event


class Ticket(models.Model):
    event_ticket = models.ForeignKey('event.Ticket', on_delete=models.RESTRICT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    order_item = models.ForeignKey('order.OrderItem', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    guest_name = models.CharField(max_length=161, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)

    def get_qrcode_svg(self, host):
        content = host + '/qrcode/?tkt=' + str(self.uuid)
        img = qrcode.make(content, image_factory=qrcode.image.svg.SvgImage, box_size=20)
        stream = BytesIO()
        img.save(stream)
        svg = mark_safe(stream.getvalue().decode())
        return svg

    def __str__(self):
        return "%s/%s" % (self.event_ticket.event.name, self.event_ticket.name)
