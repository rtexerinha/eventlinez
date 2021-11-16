from decimal import Decimal

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum, Count
from django.template.defaultfilters import slugify
from django.urls import reverse
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from address.models import City
from customer.models import Customer
from local_settings import APP_HOST


def validate_image(image):
    # max_height = 800
    # max_width = 1600
    megabyte_limit = 3.0
    if image.file.size > megabyte_limit * 1024 * 1024:
        raise ValidationError("Max file size is %sMB" % str(megabyte_limit))
    # if image.width > max_width or image.height > max_height:
    #     raise ValidationError("Height or Width is larger than what is allowed")


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


class Event(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = RichTextField(blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    event_date = models.DateTimeField(null=True, blank=True)
    address = models.CharField(max_length=300)
    city = models.ForeignKey(City, on_delete=models.PROTECT, null=True)
    promoter = models.ForeignKey(Promoter, on_delete=models.PROTECT)
    available = models.BooleanField(default=False)
    image = models.ImageField(upload_to='event', blank=False, null=False,
                              validators=[validate_image],
                              help_text='The recommended dimensions is 1600 x 838. Images with different dimensions will be resized. The image can not be greater than 3MB')
    image_sized = ImageSpecField(source='image',
                                 processors=[ResizeToFill(800, 500)],
                                 format='JPEG',
                                 options={'quality': 90})
    thumbnail = ImageSpecField(source='image',
                               processors=[ResizeToFill(265, 150)],
                               format='JPEG',
                               options={'quality': 90})
    vendors = models.ManyToManyField(Vendor, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Event'
        verbose_name_plural = 'Event'
        ordering = ['-event_date']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Event, self).save(*args, **kwargs)

    def qty_available(self):
        qty = 0
        for ticket in self.tickets.all():
            qty = qty + ticket.qty_available()
        return qty

    def qty_sould(self):
        qty = 0
        for ticket in self.tickets.all():
            qty = qty + ticket.qty_sold()
        return qty

    def quantity(self):
        qty = 0
        for ticket in self.tickets.all():
            qty = qty + ticket.quantity
        return qty

    def get_amount(self):
        from ticket.models import Ticket as TicketSould
        result = TicketSould.objects.filter(event_ticket__event=self).aggregate(Sum('price'))
        _amount = result['price__sum']
        if not _amount:
            return 0
        return _amount

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

    def __str__(self):
        return "%s/%s" % (self.event.name, self.name)


class SalesByVendor(models.Model):
    id = models.IntegerField(primary_key=True)
    vendor = models.ForeignKey(Vendor, db_column="vendor_id", on_delete=models.DO_NOTHING)
    event = models.ForeignKey(Event, db_column="event_id", on_delete=models.DO_NOTHING)
    qty = models.IntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'sales_by_vendor'
