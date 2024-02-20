from django.contrib import admin
from ticket.models import Ticket, FreeTicket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'uuid', 'event_ticket', 'customer', 'guest_name', 'created_at']
    search_fields = ['customer__first_name', 'guest_name', 'uuid']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(FreeTicket)
class FreeTicketAdmin(admin.ModelAdmin):
    list_display = ['guest_name', 'id', 'event', 'created_at', 'checkin_date']
