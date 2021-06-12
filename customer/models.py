from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='customer', unique=True)
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=120)
    address = models.CharField(max_length=250, null=True)
    city = models.CharField(max_length=250, default='NC')
    zip = models.CharField(max_length=11, default='00000')
    cellphone = models.CharField(max_length=13, null=True, blank=True)
    email = models.EmailField(unique=True)
    terms_confirmed = models.BooleanField(default=False, blank=False)

    def __str__(self):
        return self.first_name + ' ' + self.last_name
