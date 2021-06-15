from django.contrib import admin
from .models import Category, Event, Promoter
from ticket.models import Ticket


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Promoter)
class PromoterAdmin(admin.ModelAdmin):
    list_display = ['name', ]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit_price', 'available', 'event_date', 'promoter']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'event_ticket', 'customer', 'guest_name', 'created_at']
    search_fields = ['customer__first_name', 'guest_name']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
