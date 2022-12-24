from rest_framework import serializers
from .models import Ticket


class TicketSerializers(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    # order_item = models.ForeignKey('order.OrderItem', on_delete=models.PROTECT)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True)
    guest_name = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    checkin_date = serializers.DateTimeField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
