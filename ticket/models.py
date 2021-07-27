import uuid
# from io import BytesIO
#
import qrcode
import qrcode.image.svg
# from PIL import Image
# from django.core.files import File
from io import BytesIO

from django.core.validators import MinValueValidator
from django.db import models

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

    def __str__(self):
        return "%s/%s" % (self.event_ticket.event.name, self.event_ticket.name)
