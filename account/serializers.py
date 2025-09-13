
from django.contrib.auth.models import User
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class AccountSerializer(serializers.Serializer):
    user = UserSerializer(read_only=True)
    role = serializers.CharField()
