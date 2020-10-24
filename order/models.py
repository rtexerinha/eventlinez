from django.db import models


class Order(models.Model):
	token = models.CharField(max_length=250, blank=True)
	total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='GBP Order Total')
	emailAddress = models.EmailField(max_length=250, blank=True, verbose_name='Email Address')
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
	quantity = models.IntegerField()
	price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='GBP Price')
	order = models.ForeignKey(Order, on_delete=models.CASCADE)

	def sub_total(self):
		return self.quantity * self.price

	def __str__(self):
		return self.event
