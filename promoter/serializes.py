from rest_framework import serializers
from django.contrib.auth.models import User
from event.models import Promoter


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
