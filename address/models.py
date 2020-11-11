from django.db import models


class State(models.Model):
    name = models.CharField(max_length=250, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'state'
        verbose_name_plural = 'states'

    def __str__(self):
        return '{}'.format(self.name)


class City(models.Model):
    name = models.CharField(max_length=250, unique=True)
    state = models.ForeignKey(State, blank=False, on_delete=models.PROTECT)

    class Meta:
        ordering = ('name',)
        verbose_name = 'city'
        verbose_name_plural = 'cities'

    def __str__(self):
        return '{}'.format(self.name)


class Address(models.Model):
    address_name = models.CharField(max_length=250, unique=True)
    address_number = models.IntegerField(null=True, blank=True)
    city = models.ForeignKey(City, blank=True, on_delete=models.PROTECT)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    zipcode = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        ordering = ('address_name',)
        verbose_name = 'Address'
        verbose_name_plural = 'Adresses'

    def __str__(self):
        return '{}'.format(self.address_name)
