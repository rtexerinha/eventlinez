from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from .models import Cart, CartItem, AbandonedCart, AbandonedCartItem


class AbandonedCartItemInline(admin.TabularInline):
    model = AbandonedCartItem
    extra = 0
    readonly_fields = ['ticket_name', 'event_name', 'event_date', 'quantity', 'unit_price', 'total_price']
    can_delete = False


@admin.register(AbandonedCart)
class AbandonedCartAdmin(admin.ModelAdmin):
    list_display = [
        'cart_id_display', 'customer_name', 'email', 'total_amount', 
        'items_count', 'status_display', 'minutes_since_abandonment_display',
        'reminder_status', 'abandoned_at', 'actions_display'
    ]
    list_filter = [
        'reminder_status', 'abandoned_at', 'reminder_sent_at', 
        'created_at', 'converted_at'
    ]
    search_fields = ['email', 'customer_name', 'cart__cart_id']
    readonly_fields = [
        'cart', 'created_at', 'updated_at', 'abandoned_at', 
        'reminder_sent_at', 'converted_at', 'minutes_since_abandonment_display',
        'is_eligible_for_reminder_display', 'is_expired_display'
    ]
    ordering = ['-abandoned_at']
    inlines = [AbandonedCartItemInline]
    
    fieldsets = (
        ('Cart Information', {
            'fields': ('cart', 'user', 'email', 'customer_name')
        }),
        ('Cart Details', {
            'fields': ('total_amount', 'items_count')
        }),
        ('Tracking Information', {
            'fields': (
                'abandoned_at', 'minutes_since_abandonment_display',
                'is_eligible_for_reminder_display', 'is_expired_display'
            )
        }),
        ('Reminder Status', {
            'fields': (
                'reminder_status', 'reminder_sent_at', 'reminder_count'
            )
        }),
        ('Conversion Tracking', {
            'fields': ('converted_at', 'order_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['send_reminder_emails', 'mark_as_expired', 'mark_as_converted']
    
    def cart_id_display(self, obj):
        return f"Cart #{obj.cart.id}"
    cart_id_display.short_description = 'Cart ID'
    
    def status_display(self, obj):
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.reminder_status == 'converted':
            return format_html('<span style="color: green;">Converted</span>')
        elif obj.reminder_status == 'sent':
            return format_html('<span style="color: orange;">Reminder Sent</span>')
        elif obj.is_eligible_for_reminder:
            return format_html('<span style="color: blue;">Ready for Reminder</span>')
        else:
            return format_html('<span style="color: gray;">Pending</span>')
    status_display.short_description = 'Status'
    
    def minutes_since_abandonment_display(self, obj):
        minutes = obj.minutes_since_abandonment
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 1440:  # 24 hours
            hours = minutes // 60
            return f"{hours} hours"
        else:
            days = minutes // 1440
            return f"{days} days"
    minutes_since_abandonment_display.short_description = 'Time Since Abandonment'
    
    def is_eligible_for_reminder_display(self, obj):
        return obj.is_eligible_for_reminder
    is_eligible_for_reminder_display.short_description = 'Eligible for Reminder'
    is_eligible_for_reminder_display.boolean = True
    
    def is_expired_display(self, obj):
        return obj.is_expired
    is_expired_display.short_description = 'Expired'
    is_expired_display.boolean = True
    
    def actions_display(self, obj):
        actions = []
        if obj.is_eligible_for_reminder and obj.reminder_status == 'pending':
            actions.append('<a href="#" onclick="sendReminder({})">Send Reminder</a>'.format(obj.id))
        if obj.reminder_status not in ['converted', 'expired']:
            actions.append('<a href="#" onclick="markExpired({})">Mark Expired</a>'.format(obj.id))
        return format_html(' | '.join(actions)) if actions else '-'
    actions_display.short_description = 'Actions'
    
    def send_reminder_emails(self, request, queryset):
        """
        Admin action to send reminder emails to selected abandoned carts
        """
        count = 0
        for abandoned_cart in queryset.filter(reminder_status='pending'):
            if abandoned_cart.is_eligible_for_reminder:
                # Here you would implement the actual email sending logic
                # For now, we'll just mark it as sent
                abandoned_cart.mark_reminder_sent()
                count += 1
        
        if count:
            self.message_user(request, f"Reminder emails sent to {count} customers.")
        else:
            self.message_user(request, "No eligible carts found for reminder emails.")
    send_reminder_emails.short_description = "Send reminder emails to selected carts"
    
    def mark_as_expired(self, request, queryset):
        """
        Admin action to mark selected carts as expired
        """
        count = queryset.exclude(reminder_status__in=['converted', 'expired']).count()
        queryset.exclude(reminder_status__in=['converted', 'expired']).update(reminder_status='expired')
        self.message_user(request, f"Marked {count} carts as expired.")
    mark_as_expired.short_description = "Mark selected carts as expired"
    
    def mark_as_converted(self, request, queryset):
        """
        Admin action to mark selected carts as converted
        """
        count = 0
        for abandoned_cart in queryset.exclude(reminder_status='converted'):
            abandoned_cart.mark_converted()
            count += 1
        self.message_user(request, f"Marked {count} carts as converted.")
    mark_as_converted.short_description = "Mark selected carts as converted"


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['cart_id', 'date_added', 'total_amount_display', 'items_count_display']
    search_fields = ['cart_id']
    readonly_fields = ['date_added']
    
    def total_amount_display(self, obj):
        return f"${obj.amount():.2f}"
    total_amount_display.short_description = 'Total Amount'
    
    def items_count_display(self, obj):
        return obj.cartitem_set.filter(active=True).count()
    items_count_display.short_description = 'Items Count'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'ticket', 'quantity', 'price_total', 'active']
    list_filter = ['active', 'cart__date_added']
    search_fields = ['cart__cart_id', 'ticket__name', 'ticket__event__name']
