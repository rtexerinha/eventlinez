
from django.db import models
from django.core.validators import MinValueValidator
from django.template.loader import render_to_string
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core import mail
from django.db.models import Sum

from customer.models import Customer
from event.models import Event, Ticket


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
        message_txt = 'Message de teste'

        mail.send_mail(
            subject=subject,
            message=message_txt,
            from_email="noreply@eventlinez.com",
            recipient_list=[self.emailAddress],
            fail_silently=False,
            html_message=message
        )

    def ticket_qty(self):
        result = self.orderitem_set.aggregate(Sum('quantity'))
        if self.orderitem_set.count() == 0:
            return 0
        qty = result['quantity__sum']
        return qty

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    promo_code = models.CharField(max_length=10, null=True)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    fee = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    def sub_total(self):
        return self.quantity * self.price

    def __str__(self):
        return self.event.name


@receiver(post_save, sender=OrderItem)
def create_tickets(sender, instance, **kwargs):
    for i in range(0, instance.quantity):
        guest_name = None
        if instance.quantity == 1:
            guest_name = instance.order.customer.first_name + " " + instance.order.customer.last_name
        Ticket.objects.create(
            event=instance.event,
            customer=instance.order.customer,
            order_item=instance,
            price=instance.event.unit_price,
            guest_name=guest_name
        )
