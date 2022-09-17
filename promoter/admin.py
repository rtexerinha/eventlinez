from django.contrib import admin

from promoter.models import Vendor, BankAccount,Payments

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ['bank_name', 'routing_number', 'last4', 'id_bank_account']
    
    
@admin.register(Payments)
class PaymentstAdmin(admin.ModelAdmin):
    list_display = ['promoter', 'amount', 'created']

