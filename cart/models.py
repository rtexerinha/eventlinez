
from decimal import Decimal

from django.db import models
from event.models import Event
from event.models import Ticket
from django.core.validators import MinValueValidator

from local_settings import EVENTLINEZ_FEE


class Cart(models.Model):
	cart_id = models.CharField(max_length=250, blank=True)
	date_added = models.DateField(auto_now_add=True)

	class Meta:
		ordering = ['date_added']

	def amount(self):
		total = 0
		for item in self.cartitem_set.all():
			total += item.price_total()
		return total

	def __str__(self):
		return self.cart_id


class CartItem(models.Model):
	ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
	promo_code = models.CharField(max_length=10, null=True)
	quantity = models.IntegerField(validators=[MinValueValidator(0)])
	active = models.BooleanField(default=True)

	def sub_total(self):
		return self.ticket.price * self.quantity

	def fee(self):
		"""
		:return: Valor total da taxa
		"""
		fee = (self.ticket.price * Decimal(EVENTLINEZ_FEE)) * self.quantity
		return round(fee, 2)

	def price_total(self):
		return self.sub_total() + Decimal(self.fee())
