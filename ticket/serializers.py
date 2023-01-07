from rest_framework import serializers
from .models import Ticket


class TicketSerializers(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    event_ticket = serializers.CharField(read_only=True)
    vendor = serializers.CharField(read_only=True)
    guest_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    checkin_date = serializers.DateTimeField(required=True)
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'

    def update(self, instance, validated_data):
        if 'checkin_date' in validated_data:
            if instance.checkin_date:
                raise serializers.ValidationError('Ticket already checked in')
            instance.checkin_date = validated_data['checkin_date']
            instance.save()
            return instance
        raise serializers.ValidationError('Invalid checkin_date')
