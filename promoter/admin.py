from django.contrib import admin

from promoter.models import Vendor, BankAccount, Payment
from promoter.forms import PaymentForm


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'routing_number', 'account_number']
    
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['promoter', 'amount', 'created', 'description']
    form = PaymentForm

