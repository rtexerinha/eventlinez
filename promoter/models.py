from django.db import models


class Vendor(models.Model):
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250, default='')
    email = models.CharField(max_length=250, unique=True)
    phone = models.CharField(max_length=12, null=True, blank=True)
    link = models.CharField(max_length=250)

    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def __str__(self):
        return self.first_name + ' ' + self.last_name
