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

        return Partner.objects.filter(
            user=user,
            role='DOORMAN',
            event=obj.event_ticket.event
        ).exists()