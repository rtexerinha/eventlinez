from django.contrib import admin

from promoter.models import Vendor, BankAccount, Payment, Partner, PromoCode, PromoCodeUsage, Subscription
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


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['promoter', 'plan', 'status', 'monthly_fee', 'next_billing_date', 'created_date']
    list_filter = ['plan', 'status', 'created_date', 'cancelled_date']
    search_fields = ['promoter__user__email', 'promoter__user__first_name', 'promoter__user__last_name']
    readonly_fields = ['created_date', 'cancelled_date', 'expires_date']
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('promoter', 'plan', 'status', 'monthly_fee')
        }),
        ('Billing Information', {
            'fields': ('next_billing_date', 'last_billing_date', 'payment_method', 'stripe_subscription_id')
        }),
        ('Cancellation Details', {
            'fields': ('cancellation_reason', 'cancellation_feedback'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_date', 'cancelled_date', 'expires_date'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'cancelled':
            readonly.extend(['plan', 'monthly_fee', 'stripe_subscription_id'])
        return readonly

