from rest_framework import serializers
from django.contrib.auth.models import User
from event.models import Promoter, Event, Category
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


class CategoriaSerializers(serializers.Serializer):
    name = serializers.CharField(max_length=250)
    slug = serializers.SlugField(max_length=250)
    id = serializers.IntegerField()

    class Meta:
        model = Category
        fields = '__all__'


class EventSerializers(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    address = serializers.CharField()
    available = serializers.BooleanField(default=False)
    image = serializers.ImageField()
    category = serializers.CharField()
    event_date = serializers.DateTimeField()
    city = serializers.CharField()

    class Meta:
        model = Event
        fields = '__all__'

    def create(self, validated_data):

        user = self.context['request'].user
        validated_data['promoter'] = Promoter.objects.get(user=user)

        try:
            category_id = validated_data['category']
            validated_data['category'] = Category.objects.get(id=category_id)
        except Exception as e:
            raise serializers.ValidationError(e)

        try:
            city_id = validated_data['city']
            validated_data['city'] = City.objects.get(id=city_id)
        except Exception as e:
            raise serializers.ValidationError(e)

        return Event.objects.create(**validated_data)
