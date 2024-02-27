from datetime import datetime
from datetime import timedelta
from rest_framework import serializers
from .models import Ticket, FreeTicket
from event.models import Ticket as TypeTicket
from event.models import Event


class FreeTicketListSerializer(serializers.Serializer):
    event_ticket = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    guest_name = serializers.CharField(read_only=True)
    account_required = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)
    id = serializers.IntegerField(read_only=True)
    isFree = serializers.BooleanField(read_only=True)
    is_email_sent = serializers.BooleanField(read_only=True)

    class Meta:
        model = FreeTicket
        fields = '__all__'


class FreeTicketSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    guest_name = serializers.CharField(max_length=161)
    email = serializers.EmailField(max_length=80)
    event_ticket = serializers.CharField(max_length=80)
    account_required = serializers.BooleanField()
    created_at = serializers.DateTimeField(read_only=True)
    checkin_date = serializers.DateTimeField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = FreeTicket
        fields = '__all__'

    def validate(self, data):
        event_ticket = data['event_ticket']
        email = data['email']

        if FreeTicket.objects.filter(event_ticket=event_ticket, email=email).exists():
            raise serializers.ValidationError("There is already a free ticket for this event with the same email.")

        return data

    def create(self, validated_data):
        try:
            event_ticket = validated_data['event_ticket']
            validated_data['event_ticket'] = TypeTicket.objects.get(id=event_ticket)
        except Exception as e:
            raise serializers.ValidationError(e)

        return FreeTicket.objects.create(**validated_data)

    def update(self, instance, validated_data):

        if not instance:
            raise serializers.ValidationError({'error':
                                               'Ticket does not belong to this promoter.'})

        ticket_date_event = instance.event.event.event_date
        deadline = (ticket_date_event + timedelta(hours=6)
                    ).strftime("%Y-%m-%d %H:%M:%S")

        if datetime.now().strftime("%Y-%m-%d %H:%M:%S") > deadline:
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


class TicketSoldSerializers(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    event_ticket = serializers.CharField(read_only=True)
    vendor = serializers.CharField(read_only=True)
    guest_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    checkin_date = serializers.DateTimeField(required=True)
    uuid = serializers.UUIDField(read_only=True)
    isFree = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'

    def get_isFree(self, obj):
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if isinstance(instance, FreeTicket):
            data['isFree'] = instance.isFree
        return data

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
            instance.checkin_date = validated_data['checkin_date']
            instance.save()
            return instance

        raise serializers.ValidationError({'error': 'Invalid checkin_date'})
