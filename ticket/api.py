from django.db.models import Q
from rest_framework.generics import ListAPIView, UpdateAPIView
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
            return self.model.objects.filter(event_ticket__event__promoter__user=user, guest_name__contains=guest_name)
        return self.model.objects.filter(event_ticket__event__promoter__user=user)


class TicketCheckinAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        return self.model.objects.filter(event_ticket__event__promoter__user=user, id=pk)


class TicketCheckinQrcodeAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializers
    model = serializer_class.Meta.model

    lookup_field = 'uuid'

    def get_queryset(self):
        user = self.request.user
        uuid = self.kwargs['uuid']
        return self.model.objects.filter(
            event_ticket__event__promoter__user=user, uuid=uuid)
