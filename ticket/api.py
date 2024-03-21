from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import TicketSoldSerializers, TicketCreateSerializer
from .models import Ticket


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
        is_free = self.request.query_params.get('isFree', None)

        queryset = Ticket.objects.filter(Q(
            event_ticket__event__promoter__user=user,
            event_ticket__event__id=event_id) |
                                         Q(event_ticket__event__partner__user=user,
                                           event_ticket__event__id=event_id)
        ).order_by('guest_name').distinct()

        if guest_name:
            queryset = queryset.filter(guest_name__icontains=guest_name).order_by('guest_name')
        if is_free:
            queryset = queryset.filter(isFree=is_free)

        return queryset


class TicketSoldCheckinAPIView(UpdateAPIView):
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']

        queryset = self.model.objects.filter(
            Q(event_ticket__event__promoter__user=user) |
            Q(event_ticket__event__partner__user=user))

        queryset = queryset.filter(id=pk).distinct()

        return queryset


class TicketSoldDetailsAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        pk = self.kwargs['pk']
        is_free = self.request.query_params.get('isFree')

        queryset = self.model.objects.filter(
            Q(event_ticket__event__promoter__user=self.request.user) |
            Q(event_ticket__event__partner__user=self.request.user))

        queryset = queryset.filter(id=pk).distinct()

        if is_free:
            queryset = queryset.filter(isFree=is_free).distinct()

        return queryset


class TicketSoldCheckinQrcodeAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = serializer_class.Meta.model

    lookup_field = 'uuid'

    def get_queryset(self):
        user = self.request.user
        uuid = self.kwargs['uuid']

        tickets = self.model.objects.filter(
            Q(event_ticket__event__promoter__user=user, uuid=uuid) |
            Q(event_ticket__event__partner__user=user, uuid=uuid)).distinct()

        return tickets


class FreeTicketAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketCreateSerializer


@api_view(['GET', 'POST'])
def send_email_api_view(request, pk):
    user = request.user

    if request.method == 'GET':
        ticket = get_object_or_404(Ticket, id=pk, event_ticket__event__promoter__user=user)

        try:
            ticket.send_email()
        except Exception as e:
            return Response({"message": "Failed to send email", "error": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "Email sent successfully"}, status=status.HTTP_200_OK)

    return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


