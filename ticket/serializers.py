from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import Ticket


class TicketSoldSerializers(serializers.Serializer):
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

        if not instance:
            raise serializers.ValidationError({'error':
                                               'Ticket does not belong to this promoter.'})

        # Use day_event date for Full Pass tickets; fall back to parent event date
        effective_event = instance.day_event if instance.day_event else instance.event_ticket.event
        deadline = effective_event.event_date + timedelta(hours=6)

        # Both sides are timezone-aware — safe comparison
        if timezone.now() > deadline:
            raise serializers.ValidationError(
                {'error': 'Deadline to check in is over'})

        if instance.checkin_date is not None:
            raise serializers.ValidationError({'error':
                                               'Ticket has already been validated!'})
        if 'checkin_date' in validated_data:
            instance.checkin_date = validated_data['checkin_date']
            instance.save()
            return instance

        raise serializers.ValidationError({'error': 'Invalid checkin_date'})
