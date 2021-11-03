from django.contrib import admin

from promoter.models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'phone']
