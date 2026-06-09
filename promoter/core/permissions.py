from rest_framework.permissions import BasePermission
from promoter.models import Event, Partner
from event.models import Event


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


class IsDoorman(BasePermission):
    """
    Grants access if the authenticated user is a DOORMAN partner
    for at least one event, OR is a promoter (promoters can always scan).
    """
    message = "You must be assigned as a Doorman to access this resource."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Promoters always have access
        if hasattr(user, 'promoter'):
            return True
        # Doormen and Business Partners
        return Partner.objects.filter(user=user, role__in=["DOORMAN", "PARTNER"], disable=False).exists()


class IsDoormanForEvent(BasePermission):
    """
    Grants access only if the user is a DOORMAN (or promoter) for a
    specific event. The view must pass `event_id` in kwargs or query params.
    """
    message = "You are not assigned as a Doorman for this event."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        event_id = (
            view.kwargs.get("event_id")
            or view.kwargs.get("pk")
            or request.query_params.get("event_id")
            or request.data.get("event_id")
        )

        if not event_id:
            # Fall back to general doorman check
            return IsDoorman().has_permission(request, view)

        # Promoter of this event
        if Event.objects.filter(id=event_id, promoter__user=user).exists():
            return True

        # Active doorman/partner for this event
        return Partner.objects.filter(
            user=user, event_id=event_id, role__in=["DOORMAN", "PARTNER"], disable=False
        ).exists()
