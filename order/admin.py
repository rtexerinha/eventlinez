from django.contrib import admin
from .models import Order, OrderItem


class OrderItemAdmin(admin.TabularInline):
    model = OrderItem
    fieldsets = [
        ('Ticket', {'fields': ['event_ticket'], }),
        ('Promo Code', {'fields': ['promo_code'], }),
        ('Quantity', {'fields': ['quantity'], }),
        ('Price', {'fields': ['unit_price'], }),
    ]
    readonly_fields = ['ticket', 'quantity', 'unit_price', 'promo_code']
    can_delete = False
    max_num = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'emailAddress', 'created']
    list_display_links = ('id', 'emailAddress')
    search_fields = ['id', 'billingName', 'emailAddress']
    readonly_fields = ['id', 'token', 'total', 'emailAddress', 'created', 'billingName', 'billingAddress1',
                       'billingCity', 'billingPostcode', 'billingCountry', 'shippingName', 'shippingAddress1',
                       'shippingCity', 'shippingPostcode', 'shippingCountry']
    fieldsets = [
        ('ORDER INFORMATION', {'fields': ['id', 'token', 'total', 'created', 'emailAddress']}),
    ]

    inlines = [
        OrderItemAdmin,
    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
