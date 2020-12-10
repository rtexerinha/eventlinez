from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from ckeditor.fields import RichTextField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from address.models import Address
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse('shop:events_by_category', args=[self.slug])

    def __str__(self):
        return '{}'.format(self.name)


class Promoter(models.Model):
    name = models.CharField(max_length=250)
    email = models.CharField(max_length=250, unique=True)
    user = models.OneToOneField(User, on_delete=models.PROTECT, related_name='promoter', unique=True)
    address = models.CharField(max_length=250)
    city = models.CharField(max_length=250)
    zip = models.CharField(max_length=11)

    def __str__(self):
        return '{}'.format(self.name)


class Event(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    unit_price = models.DecimalField(max_digits=10,
                                     decimal_places=2,
                                     validators=[MinValueValidator(Decimal('0.00'))])
    stock = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, null=True)
    description = RichTextField(blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    event_date = models.DateTimeField(null=True, blank=True)
    event_address = models.ForeignKey(Address, blank=True, null=True, on_delete=models.PROTECT)
    promoter = models.ForeignKey(Promoter, on_delete=models.PROTECT)
    image = models.ImageField(upload_to='event', blank=False, null=False)
    thumbnail = ImageSpecField(source='image',
                               processors=[ResizeToFill(200, 159)],
                               format='JPEG',
                               options={'quality': 90})
    available = models.BooleanField(default=False)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Event'
        verbose_name_plural = 'Event'

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Event, self).save(*args, **kwargs)

    @property
    def code_promo(self):
        return self

    def get_url(self):
        return reverse('shop:product_event_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return '{}'.format(self.name)
