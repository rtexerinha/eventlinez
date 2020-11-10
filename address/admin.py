from django.contrib import admin
from .models import Address, City, State


@admin.register(State)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(City)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'state']


@admin.register(Address)
class EventAdmin(admin.ModelAdmin):
    list_display = ['address_name', 'address_number', 'city', 'latitude', 'longitude']
    # list_editable = ['price', 'stock', 'available']
