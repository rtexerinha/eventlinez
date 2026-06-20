from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import Ticket


class TicketSoldSerializers(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    event_ticket = serializers.CharField(read_only=True)
    vendor = serializers.CharField(read_only=True)
    guest_name = serializers.CharField(read_only=True)
    customer_name = serializers.SerializerMethodField()
    customer_email = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    checkin_date = serializers.DateTimeField(required=True)
    uuid = serializers.UUIDField(read_only=True)

    def get_customer_name(self, obj):
        if obj.customer:
            return f"{obj.customer.first_name} {obj.customer.last_name}".strip() or None
        return None

    def get_customer_email(self, obj):
        if obj.customer:
            return getattr(obj.customer, 'email', None) or None
        return None

    def get_order_id(self, obj):
        try:
            return obj.order_item.order.id
        except Exception:
            return None

    class Meta:
        model = Ticket
        fields = '__all__'

    def update(self, instance, validated_data):

        if not instance:
            raise serializers.ValidationError({'error':
                                               'Ticket does not belong to this promoter.'})

        # Use day_event date for Full Pass tickets; fall back to parent event date
        effective_event = instance.day_event if instance.day_event else instance.event_ticket.event
        deadline = effective_event.event_date + timedelta(hours=12)

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
