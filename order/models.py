from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.template.loader import render_to_string
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.core.mail import EmailMessage
from django.db.models import Sum

from customer.models import Customer
from event.models import Event
from promoter.models import Vendor
from ticket.models import Ticket


class Order(models.Model):
    token = models.CharField(max_length=250, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    emailAddress = models.EmailField(max_length=250, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    billingName = models.CharField(max_length=250, blank=True)
    billingAddress1 = models.CharField(max_length=250, blank=True)
    billingCity = models.CharField(max_length=250, blank=True)
    billingPostcode = models.CharField(max_length=10, blank=True)
    billingCountry = models.CharField(max_length=200, blank=True)
    shippingName = models.CharField(max_length=250, blank=True)
    shippingAddress1 = models.CharField(max_length=250, blank=True)
    shippingCity = models.CharField(max_length=250, blank=True)
    shippingPostcode = models.CharField(max_length=10, blank=True)
    shippingCountry = models.CharField(max_length=200, blank=True)
    payment_code = models.CharField(max_length=200)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created']

    def send_notification(self):
        subject = "Eventlinez - New Order #%s" % self.id

        message = render_to_string('order/email/email.html', {'order': self})
        # message_txt = 'Message de teste'

        email = EmailMessage(
            subject=subject,
            body=message,
            from_email="noreply@eventlinez.com",
            to=[self.emailAddress],
        )
        email.content_subtype = "html"

        for item in self.orderitem_set.all():
            for ticket in item.ticket_set.all():
                output_pdf = ticket.as_pdf()
                email.attach('ticket_{}.pdf'.format(ticket.id), output_pdf, 'application/pdf')
        email.send()

    def ticket_qty(self):
        """
        :return: (int) Quantidade de tickets de um evento
        """
        result = self.orderitem_set.aggregate(Sum('quantity'))
        if self.orderitem_set.count() == 0:
            return 0
        qty = result['quantity__sum']
        return qty

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    event_ticket = models.ForeignKey('event.Ticket', on_delete=models.CASCADE)
    promo_code = models.CharField(max_length=10, null=True)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, null=True)

    def sub_total(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return str(self.event_ticket)


@receiver(post_save, sender=OrderItem)
def create_tickets(sender, instance, **kwargs):
    from decimal import Decimal as _Decimal
    days = getattr(instance.event_ticket, 'days', 1) or 1
    unit_price = _Decimal(str(instance.unit_price))
    price_per_day = (unit_price / days).quantize(_Decimal('0.01'))

    for i in range(0, instance.quantity):
        guest_name = None
        if instance.quantity == 1:
            guest_name = instance.order.customer.first_name + " " + instance.order.customer.last_name

        if days > 1:
            # Full-pass: generate one ticket per day, linked to its specific event
            from event.models import FullPassEvent
            full_pass_events = {
                fp.day_number: fp.event
                for fp in FullPassEvent.objects.filter(ticket=instance.event_ticket)
            }
            for day in range(1, days + 1):
                Ticket.objects.create(
                    event_ticket=instance.event_ticket,
                    customer=instance.order.customer,
                    order_item=instance,
                    price=price_per_day,
                    guest_name=guest_name,
                    vendor=instance.vendor,
                    day_number=day,
                    day_event=full_pass_events.get(day),
                )
        else:
            Ticket.objects.create(
                event_ticket=instance.event_ticket,
                customer=instance.order.customer,
                order_item=instance,
                price=instance.unit_price,
                guest_name=guest_name,
                vendor=instance.vendor,
                day_number=None,
            )
