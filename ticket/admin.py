from django.contrib import admin
from ticket.models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'event_ticket', 'customer', 'guest_name', 'created_at']
    search_fields = ['customer__first_name', 'guest_name']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
