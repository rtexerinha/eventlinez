from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db import models

from django.template.defaultfilters import slugify
from django.urls import reverse
from ckeditor.fields import RichTextField
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from address.models import City
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from customer.models import Customer


def validate_image(image):
    max_height = 838
    max_width = 1600
    height = image.height
    width = image.width
    if width > max_width or height > max_height:
       raise ValidationError("Height or Width is larger than what is allowed")


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
    ssn = models.CharField(max_length=12, null=True, blank=True)
    phone = models.CharField(max_length=12, null=True, blank=True)
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
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = RichTextField(blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    event_date = models.DateTimeField(null=True, blank=True)
    address = models.CharField(max_length=300)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True)
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

    def sales_info(self):
        result = self.ticket_set.all().aggregate(
            amount_sould=models.Sum('price'),
            qtd_sould=models.Count('price')
        )
        if not result['amount_sould']:
            result['amount_sould'] = 0
        if not result['qtd_sould']:
            result['qtd_sould'] = 0
        result['qtd_available'] = self.stock - result['qtd_sould']
        return result

    @property
    def code_promo(self):
        return self

    def get_url(self):
        # TODO: Entender a necessidade de ter a categoria como parâmetro da URL
        return reverse('shop:product_event_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return '{}'.format(self.name)


class Ticket(models.Model):
    name = models.CharField(max_length=80)
    event = models.ForeignKey(Event, related_name="tickets", on_delete=models.RESTRICT)
    quantity = models.IntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0))]
    )

    def qty_available(self):
        qty_sold = self.qty_sold()
        return self.quantity - qty_sold

    def qty_sold(self):
        _qty_sold = self.ticket_set.count()
        return _qty_sold
