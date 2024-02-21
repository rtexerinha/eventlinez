from django.db.models import Q
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import TicketSoldSerializers, FreeTicketSerializer, FreeTicketListSerializer
from .models import Ticket, FreeTicket
from itertools import chain


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
        ).order_by('guest_name')

        free_tickets = FreeTicket.objects.filter(
            event_ticket__event__promoter__user=user,
            event_ticket__event__id=event_id
        ).order_by('guest_name')

        if guest_name:
            queryset = queryset.filter(guest_name__icontains=guest_name).order_by('guest_name')
            free_tickets = free_tickets.filter(guest_name__icontains=guest_name).order_by('guest_name')

        return list(chain(queryset, free_tickets))


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
        tickets_sold = self.model.objects.filter(event_ticket__event__promoter__user=user, id=pk)
        tickets_free = FreeTicket.objects.filter(event_ticket__event__promoter__user=user, id=pk)
        return list(chain(tickets_sold, tickets_free))


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


# --------------------------------FreeTicket
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
            event_ticket__event__id=event_id
        )

        return queryset.order_by('guest_name')


class FreeTicketDetailsAPIView(ListAPIView):
    serializer_class = FreeTicketListSerializer
    model = serializer_class.Meta.model
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        return self.model.objects.filter(event_ticket__event__promoter__user=user, id=pk)

