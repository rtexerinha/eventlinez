from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='customer')
    first_name = models.CharField(max_length=16, unique=True)
    last_name = models.CharField(max_length=16, unique=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    cellphone = models.CharField(max_length=13, null=True, blank=True)
    email = models.CharField(max_length=32)

    def __str__(self):
        return self.first_name + ' ' + self.last_name
