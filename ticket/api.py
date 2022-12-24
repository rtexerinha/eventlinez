from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import TicketSerializers


class TicketListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        guest_name = self.request.query_params.get('guest_name', None)
        if guest_name:
            return self.model.objects.filter(event_ticket__event__promoter__user=user, guest_name=guest_name)
        return self.model.objects.filter(event_ticket__event__promoter__user=user)
