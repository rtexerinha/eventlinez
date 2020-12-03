from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.template.loader import render_to_string
from django.core import mail

from event.models import Event


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
    # promoter = models.CharField(max_length=255)

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

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    promo_code = models.CharField(max_length=10, null=True)
    price = models.DecimalField(max_digits=10,
                                decimal_places=2,
                                verbose_name='GBP Price',
                                validators=[MinValueValidator(0)])
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def sub_total(self):
        return self.quantity * self.price

    def fee(self):
        return (self.price * Decimal(settings.EVENTLINEZ_FEE)) * self.quantity

    def price_total(self):
        return self.sub_total() + Decimal(self.fee())

    def __str__(self):
        return self.event.name
