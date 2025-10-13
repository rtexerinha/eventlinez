from django.contrib import admin

from promoter.models import Vendor, BankAccount, Payment, Partner, PromoCode, PromoCodeUsage
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


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['email', 'role', 'event']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'event', 'promoter', 'discount_type', 'discount_value', 'current_uses', 'max_uses', 'is_active', 'valid_until']
    list_filter = ['discount_type', 'is_active', 'event', 'promoter', 'valid_from', 'valid_until']
    search_fields = ['code', 'event__name', 'promoter__name']
    readonly_fields = ['current_uses', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'event', 'promoter', 'description')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'max_uses_per_customer', 'current_uses')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PromoCodeUsage)
class PromoCodeUsageAdmin(admin.ModelAdmin):
    list_display = ['promo_code', 'customer_email', 'discount_amount', 'used_at', 'order_id']
    list_filter = ['promo_code__event', 'promo_code__promoter', 'used_at']
    search_fields = ['promo_code__code', 'customer_email', 'order_id']
    readonly_fields = ['used_at']

