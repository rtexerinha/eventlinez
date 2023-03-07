from datetime import timedelta
from django.db.models.functions import (ExtractMonth, ExtractDay, TruncDate)
from django.db.models import Sum
from django.db.models import F
from django.db.models import FloatField

from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes


from event.models import Event
from .serializers import PromoterSerializer, EventSerializers, CategoriaSerializers, TicketSerializers


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
        return self.model.objects.filter(promoter__user=user, id=pk)


class EventListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializers
    model = Event

    def get_queryset(self):
        name = self.request.query_params.get('name')
        state = self.request.query_params.get("state")
        queryset = Event.objects.filter(promoter__user=self.request.user)

        dt_reference = timezone.now() + timedelta(-1)

        if name:
            queryset = queryset.filter(name__icontains=name)
        if state == "previous":
            queryset = queryset.filter(event_date__lte=dt_reference)
        if state == "current":
            queryset = queryset.filter(event_date__gte=dt_reference)
        return queryset


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


class TicketAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializers


class TicketUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        ticket_id = self.kwargs['pk']
        return self.model.objects.filter(id=ticket_id)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request, event_id):
    from order.models import OrderItem
    by = request.GET["by"]

    if by == "day":
        group = TruncDate('order__created')
    elif by == "month":
        group = ExtractMonth('order__created')
    else:
        return Response(status=400)

    queryset = OrderItem.objects\
        .filter(event_ticket__event_id=event_id)\
        .annotate(group=group)\
        .values("group").annotate(value=Sum(F('quantity') * F('unit_price'), output_field=FloatField()))\
        .order_by("group")

    return Response({"data": list(queryset)})
