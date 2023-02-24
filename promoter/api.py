from datetime import timedelta

from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
