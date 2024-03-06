from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from promoter.models import Partner
from .serializers import TicketSoldSerializers, FreeTicketSerializer, FreeTicketListSerializer
from .models import Ticket, FreeTicket
from itertools import chain


def filter_tickets_by_user_and_id(user, pk, is_free=None, model=None):
    if model is None:
        raise ValueError("Model cannot be None")

    queryset = model.objects.filter(
        event_ticket__event__promoter__user=user,
        id=pk
    )
    if is_free is not None:
        queryset = queryset.filter(isFree=is_free)
    return queryset


class TicketSoldListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = Ticket

    def get_queryset(self):
        user = self.request.user
        event_id = self.request.query_params.get('event_id')
        guest_name = self.request.query_params.get('guest_name', None)
        parter = Partner.objects.filter(email=user.username).first()

        queryset = Ticket.objects.filter(Q(
            event_ticket__event__promoter__user=user,
            event_ticket__event__id=event_id) |
                                         Q(event_ticket__event__partner=parter,
                                           event_ticket__event__id=event_id)
        ).order_by('guest_name').distinct()

        free_tickets = FreeTicket.objects.filter(Q(
            event_ticket__event__promoter__user=user,
            event_ticket__event__id=event_id) | Q(event_ticket__event__id=event_id,
                                                  event_ticket__event__partner=parter)
        ).order_by('guest_name').distinct()

        if guest_name:
            queryset = queryset.filter(guest_name__icontains=guest_name).order_by('guest_name')
            free_tickets = free_tickets.filter(guest_name__icontains=guest_name).order_by('guest_name')

        return list(chain(queryset, free_tickets))


class TicketSoldCheckinAPIView(UpdateAPIView):
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        is_free = self.request.query_params.get('isFree')
        parter = Partner.objects.filter(email=user.username).first()
        ticket = self.model.objects.filter(
            Q(event_ticket__event__promoter__user=user, id=pk) |
            Q(event_ticket__event__partner=parter, id=pk)).distinct()

        if is_free:
            ticket = FreeTicket.objects.filter(
                Q(event_ticket__event__promoter__user=user, id=pk, isFree=is_free) |
                Q(event_ticket__event__partner=parter, id=pk,  isFree=is_free))
        return ticket


class TicketSoldDetailsAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        pk = self.kwargs['pk']
        is_free = self.request.query_params.get('isFree')
        partner = Partner.objects.filter(email=self.request.user.username).first()

        ticket = self.model.objects.filter(
            Q(event_ticket__event__promoter__user=self.request.user, id=pk) |
            Q(event_ticket__event__partner=partner, id=pk)).distinct()

        if is_free:
            ticket = FreeTicket.objects.filter(
                Q(event_ticket__event__promoter__user=self.request.user, id=pk, isFree=is_free) |
                Q(event_ticket__event__partner=partner, id=pk, isFree=is_free)).distinct()
        return ticket


class TicketSoldCheckinQrcodeAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    lookup_field = 'uuid'

    def get_queryset(self):
        user = self.request.user
        uuid = self.kwargs['uuid']
        partner = Partner.objects.filter(email=user.username).first()

        tickets = self.model.objects.filter(
            Q(event_ticket__event__promoter__user=user, uuid=uuid) |
            Q(event_ticket__event__partner=partner, uuid=uuid)).distinct()

        if len(tickets) == 0:
            tickets = FreeTicket.objects.filter(
                Q(event_ticket__event__promoter__user=user, uuid=uuid) |
                Q(event_ticket__event__partner=partner, uuid=uuid)).distinct()
        return tickets


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


@api_view(['GET', 'POST'])
def send_email_api_view(request, pk):
    user = request.user

    if request.method == 'GET':
        ticket = get_object_or_404(FreeTicket, id=pk, event_ticket__event__promoter__user=user)

        try:
            ticket.send_email()
        except Exception as e:
            return Response({"message": "Failed to send email", "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Email sent successfully"}, status=status.HTTP_200_OK)

    return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


