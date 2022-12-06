from rest_framework import serializers
from django.contrib.auth.models import User
from event.models import Promoter, Event, Category
from .models import Vendor
from address.models import City


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')


class PromoterSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.CharField()
    ssn = serializers.CharField()
    phone = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    zip = serializers.CharField()
    user = UserSerializer()

    class Meta:
        model = Promoter
        fields = '__all__'


class VendorSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.CharField()
    phone = serializers.CharField()
    code = serializers.CharField()
    promoter = PromoterSerializer()

    class Model:
        model = Vendor
        fields = '__all__'


class CategoriaSerializers(serializers.Serializer):
    name = serializers.CharField(max_length=250)
    slug = serializers.SlugField(max_length=250)

    class Meta:
        model = Category
        fields = '__all__'


class CitySerializers(serializers.Serializer):
    name = serializers.CharField()
    state = serializers.CharField()

    class Meta:
        model = City
        fields = '__all__'


class EventSerializers(serializers.Serializer):
    name = serializers.CharField()
    slug = serializers.SlugField(max_length=250)
    description = serializers.CharField()
    address = serializers.CharField()
    city = CitySerializers()
    available = serializers.BooleanField(default=False)
    image = serializers.ImageField()
    image_sized = serializers.ImageField()
    thumbnail = serializers.ImageField()
    category = CategoriaSerializers()
    event_date = serializers.DateTimeField()
    created = serializers.DateTimeField()
    updated = serializers.DateTimeField()

    class Meta:
        model = Event
        fields = '__all__'
