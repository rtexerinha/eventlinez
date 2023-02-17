from rest_framework import serializers
from .models import City


class CitySerializers(serializers.Serializer):
    name = serializers.CharField()
    state = serializers.CharField()
    id = serializers.IntegerField()

    class Meta:
        model = City
        fields = '__all__'
