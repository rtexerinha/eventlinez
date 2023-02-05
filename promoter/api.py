from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, ListAPIView, CreateAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
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


class EventAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        query_params = self.request.query_params
        available = query_params.get('available', None)
        name = query_params.get('name', None)

        if available and name:
            return self.model.objects.filter(promoter__user=user, available=available, name__contains=name)

        if available:
            return self.model.objects.filter(promoter__user=user, available=available)

        if name:
            return self.model.objects.filter(promoter__user=user, name__contains=name)

        return self.model.objects.filter(promoter__user=user)


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
