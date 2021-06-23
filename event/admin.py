from django.contrib import admin
from .models import Category, Event, Promoter, Ticket


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
    list_display = ['name', 'quantity', 'price', 'event']
    search_fields = ['name']
