from django.contrib import admin
from .models import Category, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit_price', 'stock', 'available', 'event_address', 'created', 'updated', 'event_date']
    # list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
