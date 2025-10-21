from django.contrib import admin
from .models import Ticket
from .models_complimentary import ComplimentaryTicket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'uuid', 'event_ticket', 'customer', 'guest_name', 'created_at']
    search_fields = ['customer__first_name', 'guest_name', 'uuid']

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(ComplimentaryTicket)
class ComplimentaryTicketAdmin(admin.ModelAdmin):
    list_display = ['guest_name', 'guest_email', 'event', 'ticket_type', 'status', 'created_at', 'checkin_date']
    list_filter = ['status', 'ticket_type', 'created_at']
    search_fields = ['guest_name', 'guest_email', 'event__name']
    readonly_fields = ['uuid', 'created_at', 'sent_at', 'checkin_date']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Guest Information', {
            'fields': ('guest_name', 'guest_email', 'guest_phone')
        }),
        ('Ticket Details', {
            'fields': ('event', 'ticket_type', 'status', 'uuid')
        }),
        ('Tracking', {
            'fields': ('issued_by', 'created_at', 'sent_at', 'checkin_date')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Only allow deletion if not checked in
        if obj and obj.checkin_date:
            return False
        return super().has_delete_permission(request, obj)
