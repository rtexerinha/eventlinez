from rest_framework.permissions import BasePermission
from promoter.models import Event, Partner 

class IsEventParticipant(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        pk = view.kwargs.get("pk")

        if not pk:
            return False

        if Event.objects.filter(id=pk, promoter__user=user).exists():
            return True

        if Partner.objects.filter(user=user, event_id=pk, role="PARTNER").exists():
            return True

        return False
