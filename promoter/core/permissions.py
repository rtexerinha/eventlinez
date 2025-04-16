from rest_framework.permissions import BasePermission
from promoter.models import Event, Partner  # ajuste o import se necessário

class IsEventParticipant(BasePermission):
    """
    Permite acesso ao evento se o usuário for:
    - Superusuário
    - Promotor do evento
    - Partner vinculado ao evento
    """

    def has_permission(self, request, view):
        user = request.user
        event_id = view.kwargs.get("pk")

        if user.is_staff:
            return True

        if not event_id:
            return False

        # Verifica se é promoter do evento
        is_promoter = Event.objects.filter(id=event_id, promoter__user=user).exists()
        # Verifica se é partner do evento
        is_partner = Partner.objects.filter(event_id=event_id, user=user).exists()

        return is_promoter or is_partner
