from django.db import models
from django.db.models import Sum
from django.template.defaultfilters import slugify
from event.models import Promoter, Event
from django.template.loader import render_to_string

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.mail import EmailMessage


class BankAccount(models.Model):
    promoter = models.OneToOneField(Promoter, blank=True, null=True, on_delete=models.CASCADE)
    id_bank_account = models.CharField(max_length=250, null=True, blank=True)
    last4 = models.CharField(max_length=4, null=True, blank=True)
    bank_name = models.CharField(max_length=250, null=True, blank=True)
    routing_number = models.CharField(max_length=64, null=True, blank=True)
    
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
        

class Payments(models.Model):
    promoter = models.ForeignKey(Promoter, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='payments', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Payments'
        verbose_name_plural = 'Payments'


def get_balance(promoter):
    from ticket.models import Ticket as TicketSould
    amout_balance = None
    amount_paid = Payment.objects.filter(promoter=promoter).aggregate(Sum('amount'))
    paid = amount_paid['amount__sum']
    montante_ingressos_vendidos = TicketSould.objects.filter(event_ticket__event__promoter=promoter)\
        .aggregate(Sum('price'))
    montante = montante_ingressos_vendidos['price__sum']
    amout_balance = montante - paid
    if not amout_balance:
        return 0
    return amout_balance

                
@receiver(post_save, sender=Payment)
def email_pay(sender, instance, **kwargs):
    if kwargs.get('created', False):
        subject = "Eventlinez - Payments Paid"
        bank_account = BankAccount.objects.filter(promoter=instance.promoter)
        print(bank_account)
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
