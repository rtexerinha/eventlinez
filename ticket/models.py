from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from customer.models import Customer
from event.models import Event


class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    order_item = models.ForeignKey('order.OrderItem', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    guest_name = models.CharField(max_length=161, blank=True, null=True)
    created_at = models.DateTimeField(auto_now=True)
