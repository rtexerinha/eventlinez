from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import PromoterSerializer, EventSerializers
from .models import Promoter


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


class EventList(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        return self.model.objects.all()
