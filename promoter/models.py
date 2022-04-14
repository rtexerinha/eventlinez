from django.db import models
from django.template.defaultfilters import slugify

from event.models import Promoter, Event


class BankAccount(models.Model):
    promoter = models.OneToOneField(Promoter, blank=True, null=True, on_delete=models.CASCADE)
    id_bank_account = models.CharField(max_length=250, null=True, blank=True)
    last4 = models.CharField(max_length=4, null=True, blank=True)
    bank_name = models.CharField(max_length=250, null=True, blank=True)
    routing_number = models.CharField(max_length=64, null=True, blank=True)


class Vendor(models.Model):
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250, default='')
    email = models.CharField(max_length=250, unique=True)
    phone = models.CharField(max_length=12, null=True, blank=True)
    code = models.CharField(max_length=100, unique=True)
    promoter = models.ForeignKey(Promoter, blank=True, null=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        self.code = slugify(self.full_name())
        super(Vendor, self).save(*args, **kwargs)

    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def __str__(self):
        return self.first_name + ' ' + self.last_name


class SalesByVendor(models.Model):
    id = models.IntegerField(primary_key=True)
    vendor = models.ForeignKey(Vendor, db_column="vendor_id", on_delete=models.DO_NOTHING)
    event = models.ForeignKey(Event, db_column="event_id", on_delete=models.DO_NOTHING)
    qty = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'sales_by_vendor'
