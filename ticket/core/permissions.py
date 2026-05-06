from rest_framework.permissions import BasePermission
from promoter.models import Partner
from event.models import Promoter

class IsDoormanAndAssignedToEvent(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return Partner.objects.filter(user=user, role='DOORMAN').exists() or Promoter.objects.filter(user=user).exists()

    def has_object_permission(self, request, view, obj):
        user = request.user

        if Promoter.objects.filter(user=user).exists():
            return True  

        # Allow if doorman is assigned to the ticket's specific day event (Full Pass)
        # or to the ticket type's parent event (regular ticket)
        ticket_event = obj.day_event if obj.day_event else obj.event_ticket.event
        return Partner.objects.filter(
            user=user,
            role='DOORMAN',
            event=ticket_event
        ).exists()