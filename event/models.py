from decimal import Decimal

from ckeditor.fields import RichTextField
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.template.defaultfilters import slugify
from django.urls import reverse
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill

from address.models import City
from customer.models import Customer


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
    account_id = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return '{}'.format(self.name)


class Event(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    description = RichTextField(blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    event_date = models.DateTimeField()
    address = models.CharField(max_length=300)
    city = models.ForeignKey(City, on_delete=models.PROTECT)
    promoter = models.ForeignKey(Promoter, on_delete=models.PROTECT)
    available = models.BooleanField(default=False)
    is_free_event = models.BooleanField(default=False, help_text='Mark this event as free')
    image = models.ImageField(upload_to='event', blank=False, null=False,
                              validators=[validate_image],
                              help_text='The recommended dimensions is 1600 x 838. '
                                        'Images with different dimensions will be resized. '
                                        'The image can not be greater than 3MB')
    image_sized = ImageSpecField(source='image',
                                 processors=[ResizeToFill(800, 500)],
                                 format='JPEG',
                                 options={'quality': 90})
    thumbnail = ImageSpecField(source='image',
                               processors=[ResizeToFill(265, 150)],
                               format='JPEG',
                               options={'quality': 90})
    vendors = models.ManyToManyField("promoter.Vendor", blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Event'
        verbose_name_plural = 'Event'
        ordering = ['-event_date']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Event, self).save(*args, **kwargs)

    def qty_available(self):
        try:
            qty = 0
            for ticket in self.tickets.all():
                qty = qty + ticket.qty_available()
            return qty
        except Exception:
            return 0

    def qty_sould(self):
        try:
            qty = 0
            for ticket in self.tickets.all():
                qty = qty + ticket.qty_sold()
            return qty
        except Exception:
            return 0

    def quantity(self):
        try:
            qty = 0
            for ticket in self.tickets.all():
                qty = qty + ticket.quantity
            return qty
        except Exception:
            return 0

    def get_amount(self):
        try:
            from ticket.models import Ticket as TicketSould
            result = TicketSould.objects.filter(event_ticket__event=self).aggregate(Sum('price'))
            _amount = result['price__sum']
            if not _amount:
                return 0
            return _amount
        except Exception:
            return 0

    @property
    def code_promo(self):
        return self

    def get_url(self):
        # TODO: Entender a necessidade de ter a categoria como parâmetro da URL
        return reverse('shop:product_event_detail', args=[self.category.slug, self.slug])

    def is_active(self):
        """Check if event is currently active (event date >= today)"""
        from django.utils import timezone
        return self.event_date >= timezone.now()

    def status(self):
        """Get event status as string"""
        return 'Active' if self.is_active() else 'Past'

    def status_class(self):
        """Get CSS class for event status"""
        return 'success' if self.is_active() else 'secondary'

    def sales_percentage(self):
        """Calculate percentage of tickets sold"""
        try:
            total_qty = self.quantity()
            if total_qty == 0:
                return 0
            return round((self.qty_sould() / total_qty) * 100, 1)
        except Exception:
            return 0

    def revenue_data(self):
        """Get revenue data for charts - simplified for now"""
        from ticket.models import Ticket as TicketSold
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        # Get ticket sales over last 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # This is a simplified version - in reality you'd want daily sales data
        total_revenue = self.get_amount()
        total_sold = self.qty_sould()

        return {
            'total_revenue': float(total_revenue) if total_revenue else 0,
            'total_sold': total_sold,
            'sales_percentage': self.sales_percentage()
        }

    def safe_image_sized_url(self):
        """Safely get the image_sized URL"""
        try:
            if self.image and self.image_sized:
                return self.image_sized.url
            elif self.image:
                return self.image.url
            return None
        except Exception:
            return self.image.url if self.image else None

    def safe_thumbnail_url(self):
        """Safely get the thumbnail URL"""
        try:
            if self.image and self.thumbnail:
                return self.thumbnail.url
            elif self.image:
                return self.image.url
            return None
        except Exception:
            return self.image.url if self.image else None

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
    sold_out = models.BooleanField(default=False)
    days = models.PositiveSmallIntegerField(
        default=1,
        help_text='Number of days this ticket covers. E.g. 3 for a Full Pass (3-day ticket).'
    )

    def qty_available(self):
        try:
            qty_sold = self.qty_sold()
            return max(0, self.quantity - qty_sold)
        except Exception:
            return 0

    def qty_sold(self):
        try:
            # For multi-day passes, count only day 1 tickets so each pass
            # is counted as one sold unit, not one per day.
            from django.db.models import Q
            _qty_sold = self.ticket_set.filter(
                Q(day_number__isnull=True) | Q(day_number=1)
            ).count()
            return _qty_sold
        except Exception:
            return 0

    def __str__(self):
        return "%s/%s" % (self.event.name, self.name)


class FullPassEvent(models.Model):
    """
    Links each day of a multi-day (Full Pass) ticket type to a specific event.
    E.g. Full Pass (3 days) -> Day 1: Event A, Day 2: Event B, Day 3: Event C
    """
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='full_pass_events'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='full_pass_ticket_days'
    )
    day_number = models.PositiveSmallIntegerField(
        help_text='Which day this event corresponds to (1, 2, 3...)'
    )

    class Meta:
        ordering = ['day_number']
        unique_together = [['ticket', 'day_number']]

    def __str__(self):
        return "%s — Day %d: %s" % (self.ticket.name, self.day_number, self.event.name)
