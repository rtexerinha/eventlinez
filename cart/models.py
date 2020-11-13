from django.db import models
from event.models import Event
from django.core.validators import MinValueValidator

from local_settings import EVENTLINEZ_FEE


class Cart(models.Model):
	cart_id = models.CharField(max_length=250, blank=True)
	date_added = models.DateField(auto_now_add=True)

	class Meta:
		ordering = ['date_added']

	def __str__(self):
		return self.cart_id


class CartItem(models.Model):
	event = models.ForeignKey(Event, on_delete=models.CASCADE)
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
	quantity = models.IntegerField(validators=[MinValueValidator(0)])
	active = models.BooleanField(default=True)

	def price_fee(self):
		return float(self.event.unit_price) * EVENTLINEZ_FEE

	def price_total(self):
		return ((float(self.event.unit_price) * EVENTLINEZ_FEE) + float(self.event.unit_price)) * float(self.quantity)

	def sub_total(self):
		return ((self.event.unit_price * EVENTLINEZ_FEE) + self.event.unit_price) * self.quantity

	def __str__(self):
		return self.event
