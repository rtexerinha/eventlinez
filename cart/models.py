from decimal import Decimal
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from event.models import Event
from event.models import Ticket
from django.core.validators import MinValueValidator

from django.conf import settings
EVENTLINEZ_FEE = getattr(settings, "EVENTLINEZ_FEE", 0.12)


class Cart(models.Model):
	cart_id = models.CharField(max_length=250, blank=True)
	date_added = models.DateField(auto_now_add=True)
	applied_promo_code = models.CharField(max_length=20, null=True, blank=True)
	promo_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

	class Meta:
		ordering = ['date_added']

	def amount(self):
		total = 0
		for item in self.cartitem_set.filter(active=True):
			total += item.price_total()
		return total

	def subtotal(self):
		"""Calculate subtotal before promo discount"""
		total = 0
		for item in self.cartitem_set.filter(active=True):
			total += item.price_total()
		return total
	
	def total_with_promo(self):
		"""Calculate total after applying promo discount"""
		subtotal = self.subtotal()
		return max(0, subtotal - self.promo_discount)

	def __str__(self):
		return self.cart_id


class CartItem(models.Model):
	ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
	cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
	promo_code = models.CharField(max_length=20, null=True)
	quantity = models.IntegerField(validators=[MinValueValidator(0)])
	active = models.BooleanField(default=True)
	vendor = models.ForeignKey("promoter.Vendor", on_delete=models.PROTECT, null=True)

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


class AbandonedCart(models.Model):
	"""
	Model to track abandoned carts for email reminders
	"""
	REMINDER_STATUS_CHOICES = [
		('pending', 'Pending'),
		('sent', 'Reminder Sent'),
		('converted', 'Converted to Order'),
		('expired', 'Expired'),
	]
	
	cart = models.OneToOneField(Cart, on_delete=models.CASCADE, related_name='abandoned_cart')
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
	email = models.EmailField()
	customer_name = models.CharField(max_length=255, blank=True)
	total_amount = models.DecimalField(max_digits=10, decimal_places=2)
	items_count = models.PositiveIntegerField()
	
	# Tracking fields
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	abandoned_at = models.DateTimeField()
	reminder_status = models.CharField(max_length=20, choices=REMINDER_STATUS_CHOICES, default='pending')
	reminder_sent_at = models.DateTimeField(null=True, blank=True)
	reminder_count = models.PositiveIntegerField(default=0)
	
	# Conversion tracking
	converted_at = models.DateTimeField(null=True, blank=True)
	order_id = models.CharField(max_length=100, null=True, blank=True)
	
	class Meta:
		ordering = ['-abandoned_at']
		verbose_name = 'Abandoned Cart'
		verbose_name_plural = 'Abandoned Carts'
		
	def __str__(self):
		return f"Abandoned Cart #{self.cart.id} - {self.email} - ${self.total_amount}"
	
	@property
	def is_eligible_for_reminder(self):
		"""
		Check if cart is eligible for reminder (30+ minutes old, no reminder sent)
		"""
		if self.reminder_status != 'pending':
			return False
			
		time_threshold = timezone.now() - timedelta(minutes=30)
		return self.abandoned_at <= time_threshold
	
	@property
	def minutes_since_abandonment(self):
		"""
		Calculate minutes since cart was abandoned
		"""
		if not self.abandoned_at:
			return 0
		delta = timezone.now() - self.abandoned_at
		return int(delta.total_seconds() / 60)
	
	@property
	def is_expired(self):
		"""
		Check if cart is expired (24+ hours old)
		"""
		if not self.abandoned_at:
			return False
		expiry_threshold = timezone.now() - timedelta(hours=24)
		return self.abandoned_at <= expiry_threshold
	
	def mark_reminder_sent(self):
		"""
		Mark that reminder email has been sent
		"""
		self.reminder_status = 'sent'
		self.reminder_sent_at = timezone.now()
		self.reminder_count += 1
		self.save()
	
	def mark_converted(self, order_id=None):
		"""
		Mark cart as converted to order
		"""
		self.reminder_status = 'converted'
		self.converted_at = timezone.now()
		if order_id:
			self.order_id = order_id
		self.save()
	
	def mark_expired(self):
		"""
		Mark cart as expired
		"""
		self.reminder_status = 'expired'
		self.save()


class AbandonedCartItem(models.Model):
	"""
	Items in abandoned cart for detailed tracking
	"""
	abandoned_cart = models.ForeignKey(AbandonedCart, on_delete=models.CASCADE, related_name='items')
	ticket_name = models.CharField(max_length=255)
	event_name = models.CharField(max_length=255)
	event_date = models.DateTimeField()
	quantity = models.PositiveIntegerField()
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)
	total_price = models.DecimalField(max_digits=10, decimal_places=2)
	
	class Meta:
		verbose_name = 'Abandoned Cart Item'
		verbose_name_plural = 'Abandoned Cart Items'
	
	def __str__(self):
		return f"{self.ticket_name} - {self.event_name} (x{self.quantity})"
