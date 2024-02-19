from django.db.models import Q
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import TicketSoldSerializers, FreeTicketSerializer, FreeTicketListSerializer
from .models import Ticket, FreeTicket


class TicketSoldListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = Ticket

    def get_queryset(self):
        user = self.request.user
        event_id = self.request.query_params.get('event_id')
        guest_name = self.request.query_params.get('guest_name', None)

        queryset = Ticket.objects.filter(
            event_ticket__event__promoter__user=user,
            event_ticket__event__id=event_id
        )

        if guest_name:
            queryset = queryset.filter(guest_name__icontains=guest_name)

        return queryset.order_by('guest_name')


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


class FreeTicketAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FreeTicketSerializer


class FreeTicketListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FreeTicketListSerializer
    model = FreeTicket

    def get_queryset(self):
        event_id = self.request.query_params.get('event_id')
        queryset = FreeTicket.objects.filter(
            event__id=event_id
        )

        return queryset.order_by('guest_name')


class FreeTicketDetailsAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FreeTicketListSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        return self.model.objects.filter(event__promoter__user=user, id=pk)


# FREE TICKET CHECKIN
class FreeTicketCheckinAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FreeTicketSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        return self.model.objects.filter(event__promoter__user=user, id=pk)
