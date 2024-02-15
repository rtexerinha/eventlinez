from datetime import timedelta

from django.db import IntegrityError
from django.db.models.functions import (ExtractMonth, ExtractDay, TruncDate, ExtractYear)
from django.db.models import Sum, Q
from django.db.models import F
from django.db.models import FloatField

from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework import status

from account.api import get_user_role
from event.models import Event
from .models import Partner
from .serializers import PromoterSerializer, EventSerializers, CategoriaSerializers, TicketTypeSerializers, \
     PartnerSerializer, PartnerCreateSerializer
from promoter.util import transform_month
from django.contrib.auth.models import User


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })


class PromoterListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PromoterSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        return self.model.objects.filter(user=user)


class EventDetailsAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        queryset = self.model.objects.filter(promoter__user=user, id=pk)

        queryset_with_roles = []

        for event in queryset:
            event.role = get_user_role(self.request.user, event)
            queryset_with_roles.append(event)

        return queryset_with_roles


class EventCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializers
    model = Event


class EventListAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializers
    model = Event

    def get_queryset(self):
        name = self.request.query_params.get('name')
        state = self.request.query_params.get("state")
        queryset = Event.objects.filter(
            Q(partner__user=self.request.user) | Q(promoter__user=self.request.user)).distinct()

        dt_reference = timezone.now() + timedelta(-1)

        if name:
            queryset = queryset.filter(name__icontains=name)
        if state == "previous":
            queryset = queryset.filter(event_date__lte=dt_reference)
        if state == "current":
            queryset = queryset.filter(event_date__gte=dt_reference)

        queryset_with_roles = []

        for event in queryset:
            event.role = get_user_role(self.request.user, event)
            queryset_with_roles.append(event)

        return queryset_with_roles


class EventUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        return self.model.objects.filter(promoter__user=user)


class CategoryListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CategoriaSerializers
    model = serializer_class.Meta.model
    queryset = model.objects.all()


class TicketTypeAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketTypeSerializers


class TicketTypeUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketTypeSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        ticket_id = self.kwargs['pk']
        return self.model.objects.filter(id=ticket_id)


class TicketTypeListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketTypeSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        queryset = self.model.objects.filter(event_id=event_id)
        return queryset


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request, event_id):
    from order.models import OrderItem
    by = request.GET["by"]

    queryset = OrderItem.objects.filter(event_ticket__event_id=event_id)
    calc = Sum(F('quantity'))

    if by == "day":
        group = TruncDate('order__created')
        queryset = queryset .annotate(group=group) \
            .values("group").annotate(value=calc).order_by("group")
        data = list(queryset)
    elif by == "month":
        queryset = queryset.annotate(
                    month=ExtractMonth('order__created'),
                    year=ExtractYear('order__created')).\
            values("month", "year").annotate(value=calc).order_by("year", "month")
        data = list(map(transform_month, list(queryset)))
    else:
        return Response(status=400)

    return Response({"data": data})


class PartnerUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnerSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        partner_id = self.kwargs['pk']
        return self.model.objects.filter(id=partner_id)


class PartnerCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnerCreateSerializer


class PartnerListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnerSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        query = self.model.objects.filter(event_id=event_id)
        return query


