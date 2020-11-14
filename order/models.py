from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator


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

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return str(self.id)


class OrderItem(models.Model):
    event = models.CharField(max_length=250)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    price = models.DecimalField(max_digits=10,
                                decimal_places=2,
                                verbose_name='GBP Price',
                                validators=[MinValueValidator(0)])
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    def price_fee(self):
        return (self.price * settings.EVENTLINEZ_FEE) + self.price

    def sub_total(self):
        return self.quantity * (self.price * settings.EVENTLINEZ_FEE) + self.price

    def __str__(self):
        return self.event
