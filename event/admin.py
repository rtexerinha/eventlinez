from django.contrib import admin
from .models import Category, Event, Promoter


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Promoter)
class PromoterAdmin(admin.ModelAdmin):
    list_display = ['name', ]


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit_price', 'stock', 'event_address', 'available', 'event_date', 'promoter']
    # list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
