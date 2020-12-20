
from decimal import Decimal

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
	promo_code = models.CharField(max_length=10, null=True)
	quantity = models.IntegerField(validators=[MinValueValidator(0)])
	active = models.BooleanField(default=True)

	def sub_total(self):
		return self.event.unit_price * self.quantity

	def fee(self):
		"""
		:return: Valor total da taxa
		"""
		fee = (self.event.unit_price * Decimal(EVENTLINEZ_FEE)) * self.quantity
		return round(fee, 2)

	def price_total(self):
		return self.sub_total() + Decimal(self.fee())

	def __str__(self):
		return self.event
