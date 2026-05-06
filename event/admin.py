from django.contrib import admin
from .models import Category, Event, FullPassEvent, Promoter, Ticket


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Promoter)
class PromoterAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone']
    search_fields = ['name', 'email']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'available', 'event_date', 'promoter']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'price', 'days', 'event']
    search_fields = ['name']
    list_filter = ['days']


@admin.register(FullPassEvent)
class FullPassEventAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'day_number', 'event']
    list_filter = ['day_number']
    search_fields = ['ticket__name', 'event__name']
