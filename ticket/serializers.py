from datetime import datetime
from datetime import timedelta
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

        if not instance:
            raise serializers.ValidationError({'error':
                                               'Ticket does not belong to this promoter.'})

        ticket_date_event = instance.event_ticket.event.event_date
        deadline = (ticket_date_event + timedelta(hours=6)
                    ).strftime("%Y-%m-%d %H:%M:%S")

        if datetime.now().strftime("%Y-%m-%d %H:%M:%S") > deadline:
            raise serializers.ValidationError(
                {'error': 'Deadline to check in is over'})

        if instance.checkin_date is not None:
            raise serializers.ValidationError({'error':
                                               'Ticket has already been validated!'})
        if 'checkin_date' in validated_data:
            if instance.checkin_date:
                raise serializers.ValidationError(
                    {'error': 'Ticket already checked in'})
            instance.checkin_date = validated_data['checkin_date']
            instance.save()
            return instance

        raise serializers.ValidationError({'error': 'Invalid checkin_date'})
