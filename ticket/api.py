from django.db.models import Q
from rest_framework.generics import ListAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import TicketSoldSerializers
from .models import Ticket
from event.models import Promoter

from .core.permissions import IsDoormanAndAssignedToEvent
from promoter.models import Partner 


class TicketSoldListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = Ticket

    def get_queryset(self):
        user = self.request.user
        event_id = self.request.query_params.get('event_id')
        guest_name = self.request.query_params.get('guest_name', None)

        queryset = Ticket.objects.filter(
            event_ticket__event__promoter__user=user
        ).filter(
            Q(event_ticket__event__id=event_id) | Q(day_event__id=event_id)
        )

        if guest_name:
            queryset = queryset.filter(guest_name__icontains=guest_name)

        return queryset.order_by('guest_name')


class TicketSoldCheckinAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated, IsDoormanAndAssignedToEvent)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']

        if Promoter.objects.filter(user=user).exists():
            return self.model.objects.filter(
                event_ticket__event__promoter__user=user,
                id=pk
            )

        if Partner.objects.filter(user=user, role='DOORMAN').exists():
            from django.db.models import Q
            return self.model.objects.filter(
                Q(event_ticket__event__partner__user=user, day_event__isnull=True) |
                Q(day_event__partner__user=user),
                id=pk
            )

        return self.model.objects.none()


class TicketSoldDetailsAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        return self.model.objects.filter(event_ticket__event__promoter__user=user, id=pk)


class TicketSoldCheckinQrcodeAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated, IsDoormanAndAssignedToEvent)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model
    lookup_field = 'uuid'

    def get_queryset(self):
        from django.db.models import Q
        user = self.request.user
        uuid = self.kwargs['uuid']

        if Promoter.objects.filter(user=user).exists():
            return self.model.objects.filter(
                event_ticket__event__promoter__user=user,
                uuid=uuid
            )

        if Partner.objects.filter(user=user, role='DOORMAN').exists():
            # For Full Pass tickets the authoritative event is day_event, not the parent event
            return self.model.objects.filter(
                Q(event_ticket__event__partner__user=user, day_event__isnull=True) |
                Q(day_event__partner__user=user),
                uuid=uuid
            )

        return self.model.objects.none()
