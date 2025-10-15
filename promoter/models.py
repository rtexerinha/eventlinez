from django.db import models
from django.db.models import Sum
from django.template.defaultfilters import slugify
from event.models import Promoter, Event
from django.template.loader import render_to_string
from django.contrib.auth.models import User

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import EmailMessage
from django.core.validators import RegexValidator

from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

numeric = RegexValidator(r'^[0-9+]', 'Only digit numeric.')

alpha = RegexValidator(r'^[a-zA-Z]+', 'Only letters')


def min_validation_none(value):
    if len(value) < 9:
        raise ValidationError("{} is invalid, must have more than 9 characters". format(value))


class BankAccount(models.Model):
    promoter = models.OneToOneField(Promoter, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=12, validators=[numeric, min_validation_none])
    bank_name = models.CharField(max_length=250, validators=[alpha])
    routing_number = models.CharField(max_length=12, validators=[numeric, min_validation_none])

    def __str__(self):
        return self.bank_name


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


class Payment(models.Model):
    promoter = models.ForeignKey(Promoter, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='payments', blank=True, null=True)
    description = models.CharField(max_length=250)

    class Meta:
        verbose_name = 'Payments'
        verbose_name_plural = 'Payments'


def get_balance(promoter):
    from ticket.models import Ticket as TicketSould
    amout_balance = None
    amount_paid = Payment.objects.filter(promoter=promoter).aggregate(Sum('amount'))['amount__sum']
    amout_ticket = TicketSould.objects.filter(event_ticket__event__promoter=promoter) \
        .aggregate(Sum('price'))['price__sum']
    if not amout_ticket:
        return 0
    if not amount_paid:
        return amout_ticket
    amout_balance = amout_ticket - amount_paid
    return amout_balance


@receiver(post_save, sender=Payment)
def email_pay(sender, instance, **kwargs):
    if kwargs.get('created', False):
        subject = "Eventlinez - Payments Paid"
        bank_account = BankAccount.objects.filter(promoter=instance.promoter)
        message = render_to_string('payout/email/payout_success.html',
                                   {'payout': instance, 'bank_account': bank_account[0],
                                    'promoter': instance.promoter.email})
        from_email = 'noreply@eventlinez.com'
        email_payout = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=[instance.promoter.email],
        )
        email_payout.content_subtype = "html"
        email_payout.send()


class Partner(models.Model):
    ROLES = [
        ("DOORMAN", "Doorman"),
        ("PARTNER", "Businnes Partner")
    ]
    email = models.EmailField(blank=False, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(choices=ROLES, max_length=40)
    disable = models.BooleanField(default=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["email", "event"]]


@receiver(post_save, sender=Partner)
def email_partner(sender, instance, **kwargs):
    username = User.objects.get(username=instance.email)
    if kwargs.get('created', False):
        subject = "Eventlinez - Notification of Role Assignment in Event"
        message = render_to_string('partner/email/partner-email.html',
                                   {'partner': instance, 'user': username})

        email_new_partner = EmailMessage(
            subject=subject,
            body=message,
            from_email='noreply@eventlinez.com',
            to=[instance.email],
        )
        email_new_partner.content_subtype = "html"
        email_new_partner.send()


class PromoCode(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('amount', 'Dollar Amount'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='promo_codes')
    promoter = models.ForeignKey(Promoter, on_delete=models.CASCADE, related_name='promo_codes')
    
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Usage limits
    max_uses = models.PositiveIntegerField(default=1, help_text="Maximum number of times this code can be used")
    max_uses_per_customer = models.PositiveIntegerField(default=1, help_text="Maximum uses per customer")
    current_uses = models.PositiveIntegerField(default=0)
    
    # Date restrictions
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(blank=True, help_text="Internal description for this promo code")
    
    class Meta:
        verbose_name = 'Promo Code'
        verbose_name_plural = 'Promo Codes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.event.name}"
    
    def is_valid(self):
        """Check if promo code is currently valid"""
        now = timezone.now()
        return (
            self.is_active and 
            self.valid_from <= now <= self.valid_until and
            self.current_uses < self.max_uses
        )
    
    def can_be_used_by_customer(self, customer_email):
        """Check if customer can use this promo code"""
        if not self.is_valid():
            return False, "Promo code is not valid or has expired"
        
        # Check customer usage limit
        customer_uses = PromoCodeUsage.objects.filter(
            promo_code=self,
            customer_email=customer_email
        ).count()
        
        if customer_uses >= self.max_uses_per_customer:
            return False, "You have already used this promo code the maximum number of times"
        
        return True, "Promo code is valid"
    
    def calculate_discount(self, subtotal):
        """Calculate discount amount for given subtotal"""
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / Decimal('100')
        else:  # amount
            discount = min(self.discount_value, subtotal)  # Can't discount more than subtotal
        
        return round(discount, 2)
    
    def get_discount_display(self):
        """Get human readable discount description"""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}% off"
        else:
            return f"${self.discount_value} off"


class PromoCodeUsage(models.Model):
    """Track promo code usage per customer"""
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='usages')
    customer_email = models.EmailField()
    order_id = models.CharField(max_length=100, null=True, blank=True)
    used_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Promo Code Usage'
        verbose_name_plural = 'Promo Code Usages'
        ordering = ['-used_at']
    
    def __str__(self):
        return f"{self.promo_code.code} used by {self.customer_email}"


class Subscription(models.Model):
    """Promoter subscription management"""
    PLAN_CHOICES = [
        ('basic', 'Basic Plan'),
        ('pro', 'Promoter Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    CANCELLATION_REASONS = [
        ('too_expensive', 'Too expensive'),
        ('not_using_features', 'Not using enough features'),
        ('found_alternative', 'Found a better alternative'),
        ('technical_issues', 'Technical issues'),
        ('business_closure', 'Closing business'),
        ('other', 'Other'),
    ]
    
    promoter = models.OneToOneField(Promoter, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='pro')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Billing information
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('29.99'))
    next_billing_date = models.DateTimeField()
    last_billing_date = models.DateTimeField(null=True, blank=True)
    
    # Subscription lifecycle
    created_date = models.DateTimeField(auto_now_add=True)
    cancelled_date = models.DateTimeField(null=True, blank=True)
    expires_date = models.DateTimeField(null=True, blank=True)
    
    # Cancellation details
    cancellation_reason = models.CharField(
        max_length=50, 
        choices=CANCELLATION_REASONS, 
        null=True, 
        blank=True
    )
    cancellation_feedback = models.TextField(blank=True, null=True)
    
    # Payment details
    payment_method = models.CharField(max_length=100, default='•••• •••• •••• 4242')
    stripe_subscription_id = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name = 'Subscription'
        verbose_name_plural = 'Subscriptions'
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.promoter.user.email} - {self.get_plan_display()} ({self.get_status_display()})"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status == 'active'
    
    @property
    def plan_name(self):
        """Get human-readable plan name"""
        return self.get_plan_display()
    
    def cancel(self, reason=None, feedback=None):
        """Cancel the subscription"""
        from django.utils import timezone
        
        self.status = 'cancelled'
        self.cancelled_date = timezone.now()
        self.expires_date = self.next_billing_date  # Access until next billing date
        
        if reason:
            self.cancellation_reason = reason
        if feedback:
            self.cancellation_feedback = feedback
            
        self.save()
    
    def reactivate(self):
        """Reactivate a cancelled subscription"""
        from django.utils import timezone
        from datetime import timedelta
        
        if self.status == 'cancelled':
            self.status = 'active'
            self.cancelled_date = None
            self.expires_date = None
            self.cancellation_reason = None
            self.cancellation_feedback = None
            
            # Set next billing date to 30 days from now
            self.next_billing_date = timezone.now() + timedelta(days=30)
            self.save()
            return True
        return False

