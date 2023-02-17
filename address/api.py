from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from .serializers import CitySerializers
from .models import City


class CityListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CitySerializers
    queryset = City.objects.all()
