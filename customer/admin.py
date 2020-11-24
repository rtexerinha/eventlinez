from django.contrib import admin

# Register your models here
from customer.models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'cellphone', 'email']


