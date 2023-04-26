from django.db.models import Q
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import TicketSoldSerializers


class TicketSoldListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        guest_name = self.request.query_params.get('guest_name', None)
        event_name = self.request.query_params.get('event_name', None)

        if event_name and guest_name:
            return self.model.objects.filter(event_ticket__event__promoter__user=user,
                                             event_ticket__event__name__contains=event_name,
                                             guest_name__icontains=guest_name)
        if guest_name:
            return self.model.objects.filter(event_ticket__event__promoter__user=user, guest_name__icontains=guest_name)
        if event_name:
            return self.model.objects.filter(event_ticket__event__promoter__user=user, event_ticket__event__name__contains=event_name)
        return self.model.objects.filter(event_ticket__event__promoter__user=user)


class TicketSoldCheckinAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        return self.model.objects.filter(event_ticket__event__promoter__user=user, id=pk)


class TicketSoldDetailsAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        return self.model.objects.filter(event_ticket__event__promoter__user=user, id=pk)


class TicketSoldCheckinQrcodeAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    lookup_field = 'uuid'

    def get_queryset(self):
        user = self.request.user
        uuid = self.kwargs['uuid']
        return self.model.objects.filter(
            event_ticket__event__promoter__user=user, uuid=uuid)
