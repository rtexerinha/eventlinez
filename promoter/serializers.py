import base64
import urllib.parse

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework import serializers

from address.models import City
from event.models import Promoter, Event, Category, Ticket
from promoter.models import Partner, PromoCode, PromoCodeUsage


class Base64ImageField(serializers.ImageField):
    """
    Um campo personalizado para lidar com imagens codificadas em base64.
    """

    def to_internal_value(self, data):
        """
        Converte uma string base64 em um arquivo de imagem.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            # Decodifica a string base64
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'file.{ext}')

        return super().to_internal_value(data)


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


class EventListSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    address = serializers.CharField()
    available = serializers.BooleanField(default=False)
    image = Base64ImageField()
    category = serializers.CharField()
    event_date = serializers.DateTimeField()
    city = serializers.CharField()
    id = serializers.IntegerField(read_only=True)
    qty_available = serializers.SerializerMethodField(read_only=True)
    qty_sould = serializers.SerializerMethodField(read_only=True)
    quantity = serializers.SerializerMethodField(read_only=True)
    amount = serializers.SerializerMethodField(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)
    role = serializers.CharField(read_only=True)

    class Meta:
        model = Event
        fields = '__all__'

    def get_qty_available(self, obj):
        return obj.qty_available()

    def get_qty_sould(self, obj):
        return obj.qty_sould()

    def get_quantity(self, obj):
        return obj.quantity()

    def get_amount(self, obj):
        return obj.get_amount()

    def get_url(self, obj):
        return obj.get_url()


class EventSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    address = serializers.CharField()
    available = serializers.BooleanField(default=False)
    image = Base64ImageField()
    category = serializers.CharField()
    event_date = serializers.DateTimeField()
    city = serializers.CharField()
    id = serializers.IntegerField(read_only=True)

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

    def update(self, instance, validated_data):

        try:
            if 'category' in validated_data:
                category_id = validated_data['category']
                instance.category = Category.objects.get(id=category_id)
        except Exception as e:
            raise serializers.ValidationError(e)

        try:
            if 'city' in validated_data:
                city_id = validated_data['city']
                instance.city = City.objects.get(id=city_id)
        except Exception as e:
            raise serializers.ValidationError(e)

        if 'name' in validated_data:
            instance.name = validated_data['name']

        if 'description' in validated_data:
            instance.description = validated_data['description']

        if 'address' in validated_data:
            instance.address = validated_data['address']

        if 'available' in validated_data:
            instance.available = validated_data['available']

        if 'image' in validated_data:
            instance.image = validated_data['image']

        if 'event_date' in validated_data:
            instance.event_date = validated_data['event_date']

        instance.save()

        return instance


class TicketTypeSerializers(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=80)
    event = serializers.CharField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(decimal_places=2, max_digits=10)
    sold_out = serializers.BooleanField(default=False)
    qty_sold = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'

    def get_qty_sold(self, obj):
        """Get the number of tickets sold for this ticket type"""
        try:
            return obj.qty_sold()
        except Exception:
            return 0

    def create(self, validated_data):

        try:
            event_id = validated_data['event']
            validated_data['event'] = Event.objects.get(id=event_id)
        except Exception as e:
            raise serializers.ValidationError(e)

        return Ticket.objects.create(**validated_data)

    def update(self, instance, validated_data):

        try:
            if 'event' in validated_data:
                event_id = validated_data['event']
                instance.event = Event.objects.get(id=event_id)
        except Exception as e:
            raise serializers.ValidationError(e)

        if 'name' in validated_data:
            instance.name = validated_data['name']

        if 'quantity' in validated_data:
            instance.quantity = validated_data['quantity']

        if 'price' in validated_data:
            instance.price = validated_data['price']
        
        if 'sold_out' in validated_data:
            instance.sold_out = validated_data['sold_out']

        instance.save()

        return instance


class PartnerCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.CharField()
    disable = serializers.BooleanField(default=False)
    event_id = serializers.IntegerField()

    class Meta:
        model = Partner
        fields = ('email', 'role', 'event_id', 'disable')

    def validate_email(self, email):
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('The user with this email does not exist. The partner needs to register first.')

        queryset = Partner.objects.filter(user__username=email, event=self.initial_data["event_id"])
        if queryset.count() != 0:
            raise serializers.ValidationError('The user is already a partner for this event')

        if self.context["request"].user.email == email:
            raise serializers.ValidationError('The event promoter cannot be a partner')

        return email

    def validate_event_id(self, event_id):
        try:
            Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError('Event with provided ID does not exist')
        return event_id

    def create(self, validated_data):
        user = User.objects.get(username=validated_data["email"])
        return Partner.objects.create(user=user, **validated_data)


class PartnerSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    email = serializers.CharField()
    user = UserSerializer()
    role = serializers.CharField()
    disable = serializers.BooleanField(default=False)
    event = serializers.CharField()
    created_at = serializers.DateTimeField()

    class Meta:
        model = Partner
        fields = '__all__'

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


# ─────────────────────────────────────────────
#  Promo Code Serializers
# ─────────────────────────────────────────────

class PromoCodeUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCodeUsage
        fields = ('id', 'customer_email', 'order_id', 'used_at', 'discount_amount')
        read_only_fields = fields


class PromoCodeSerializer(serializers.ModelSerializer):
    discount_display = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()
    uses_remaining = serializers.SerializerMethodField()
    event_name = serializers.CharField(source='event.name', read_only=True)
    usages = PromoCodeUsageSerializer(many=True, read_only=True)

    class Meta:
        model = PromoCode
        fields = (
            'id', 'code', 'event', 'event_name',
            'discount_type', 'discount_value',
            'max_uses', 'max_uses_per_customer', 'current_uses', 'uses_remaining',
            'valid_from', 'valid_until',
            'is_active', 'is_valid',
            'description', 'discount_display',
            'created_at', 'updated_at',
            'usages',
        )
        read_only_fields = ('id', 'current_uses', 'created_at', 'updated_at', 'usages')

    def get_discount_display(self, obj):
        return obj.get_discount_display()

    def get_is_valid(self, obj):
        return obj.is_valid()

    def get_uses_remaining(self, obj):
        return max(0, obj.max_uses - obj.current_uses)

    def validate_event(self, event):
        user = self.context['request'].user
        if not hasattr(user, 'promoter'):
            raise serializers.ValidationError('You are not a promoter.')
        if event.promoter.user != user:
            raise serializers.ValidationError('You can only create promo codes for your own events.')
        return event

    def validate(self, data):
        valid_from = data.get('valid_from')
        valid_until = data.get('valid_until')
        if valid_from and valid_until and valid_from >= valid_until:
            raise serializers.ValidationError({'valid_until': 'valid_until must be after valid_from.'})
        if data.get('discount_type') == 'percentage':
            if not (0 < float(data.get('discount_value', 0)) <= 100):
                raise serializers.ValidationError({'discount_value': 'Percentage must be between 1 and 100.'})
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['promoter'] = user.promoter
        return PromoCode.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('event', None)   # event cannot be changed
        validated_data.pop('promoter', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class PromoCodeValidateSerializer(serializers.Serializer):
    """Public-facing serializer: validate a promo code for a cart subtotal."""
    code = serializers.CharField(max_length=20)
    event_id = serializers.IntegerField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)


# ─────────────────────────────────────────────
#  Guest List (Complimentary Ticket) Serializers
# ─────────────────────────────────────────────

class ComplimentaryTicketSerializer(serializers.Serializer):
    """Read serializer for ComplimentaryTicket."""
    from ticket.models_complimentary import ComplimentaryTicket as _CT

    id = serializers.IntegerField(read_only=True)
    uuid = serializers.UUIDField(read_only=True)
    event = serializers.IntegerField(source='event.id', read_only=True)
    event_name = serializers.CharField(source='event.name', read_only=True)
    guest_name = serializers.CharField()
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(allow_blank=True, required=False)
    ticket_type = serializers.ChoiceField(choices=_CT.TICKET_TYPE_CHOICES)
    ticket_type_display = serializers.SerializerMethodField()
    status = serializers.ChoiceField(choices=_CT.STATUS_CHOICES, read_only=True)
    status_display = serializers.SerializerMethodField()
    notes = serializers.CharField(allow_blank=True, required=False)
    qr_code_url = serializers.CharField(read_only=True)
    whatsapp_url = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    sent_at = serializers.DateTimeField(read_only=True)
    checkin_date = serializers.DateTimeField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        from ticket.models_complimentary import ComplimentaryTicket
        model = ComplimentaryTicket
        fields = '__all__'

    def get_ticket_type_display(self, obj):
        return obj.get_ticket_type_display()

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_whatsapp_url(self, obj):
        message = (
            f"🎉 Your FREE Ticket for {obj.event.name}\n\n"
            f"👤 Guest: {obj.guest_name}\n"
            f"🎫 Type: {obj.get_ticket_type_display()}\n"
            f"📅 Date: {obj.event.event_date.strftime('%B %d, %Y at %I:%M %p')}\n"
            f"📍 Location: {obj.event.address}, {obj.event.city}\n\n"
            f"🔗 Your ticket: {obj.qr_code_url}\n\n"
            f"Show this QR code at the entrance!"
        )
        encoded = urllib.parse.quote(message)
        if obj.guest_phone:
            phone = ''.join(filter(str.isdigit, obj.guest_phone))
            return f"https://wa.me/{phone}?text={encoded}"
        return f"https://wa.me/?text={encoded}"


class ComplimentaryTicketCreateSerializer(serializers.Serializer):
    from ticket.models_complimentary import ComplimentaryTicket as _CT

    event_id = serializers.IntegerField(write_only=True)
    guest_name = serializers.CharField(max_length=200)
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(max_length=20, allow_blank=True, required=False, default='')
    ticket_type = serializers.ChoiceField(choices=_CT.TICKET_TYPE_CHOICES, default='GUEST_LIST')
    notes = serializers.CharField(allow_blank=True, required=False, default='')
    send_email = serializers.BooleanField(default=False, write_only=True)

    def validate_event_id(self, value):
        user = self.context['request'].user
        try:
            event = Event.objects.get(pk=value, promoter__user=user)
        except Event.DoesNotExist:
            raise serializers.ValidationError('Event not found or you are not the promoter.')
        return value

    def create(self, validated_data):
        from ticket.models_complimentary import ComplimentaryTicket
        from ticket.views_complimentary import send_complimentary_ticket_email

        send_email = validated_data.pop('send_email', False)
        event_id = validated_data.pop('event_id')
        event = Event.objects.get(pk=event_id)
        user = self.context['request'].user

        ticket = ComplimentaryTicket.objects.create(
            event=event,
            issued_by=user.promoter,
            **validated_data
        )

        if send_email:
            if send_complimentary_ticket_email(ticket):
                ticket.mark_as_sent()

        return ticket


class BulkGuestCreateSerializer(serializers.Serializer):
    from ticket.models_complimentary import ComplimentaryTicket as _CT

    event_id = serializers.IntegerField()
    ticket_type = serializers.ChoiceField(choices=_CT.TICKET_TYPE_CHOICES, default='GUEST_LIST')
    send_immediately = serializers.BooleanField(default=False)
    guests = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=500,
    )

    def validate_event_id(self, value):
        user = self.context['request'].user
        try:
            Event.objects.get(pk=value, promoter__user=user)
        except Event.DoesNotExist:
            raise serializers.ValidationError('Event not found or you are not the promoter.')
        return value

    def validate_guests(self, guests):
        errors = []
        for i, g in enumerate(guests):
            if not g.get('name'):
                errors.append(f'Guest {i+1}: name is required.')
            if not g.get('email'):
                errors.append(f'Guest {i+1}: email is required.')
        if errors:
            raise serializers.ValidationError(errors)
        return guests


# ─────────────────────────────────────────────
#  Doorman Serializers
# ─────────────────────────────────────────────

class DoormanEventSerializer(serializers.Serializer):
    """Events a doorman is assigned to."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    event_date = serializers.DateTimeField()
    address = serializers.CharField()
    city = serializers.CharField()
    image = Base64ImageField(required=False, allow_null=True)
    # Live checkin counters
    total_tickets = serializers.SerializerMethodField()
    checked_in = serializers.SerializerMethodField()
    pending = serializers.SerializerMethodField()
    # Guest list counters
    total_guests = serializers.SerializerMethodField()
    guests_checked_in = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = '__all__'

    def get_total_tickets(self, obj):
        from ticket.models import Ticket
        return Ticket.objects.filter(event_ticket__event=obj).count()

    def get_checked_in(self, obj):
        from ticket.models import Ticket
        return Ticket.objects.filter(event_ticket__event=obj, checkin_date__isnull=False).count()

    def get_pending(self, obj):
        from ticket.models import Ticket
        return Ticket.objects.filter(event_ticket__event=obj, checkin_date__isnull=True).count()

    def get_total_guests(self, obj):
        from ticket.models_complimentary import ComplimentaryTicket
        return ComplimentaryTicket.objects.filter(event=obj).exclude(status='CANCELLED').count()

    def get_guests_checked_in(self, obj):
        from ticket.models_complimentary import ComplimentaryTicket
        return ComplimentaryTicket.objects.filter(event=obj, status='CHECKED_IN').count()


class TicketScanResultSerializer(serializers.Serializer):
    """Returned after scanning a paid ticket QR code."""
    success = serializers.BooleanField()
    message = serializers.CharField()
    already_checked_in = serializers.BooleanField(default=False)
    ticket_id = serializers.IntegerField(required=False)
    guest_name = serializers.CharField(required=False, allow_null=True)
    event_name = serializers.CharField(required=False)
    ticket_type = serializers.CharField(required=False)
    checked_in_at = serializers.DateTimeField(required=False, allow_null=True)
    # Only filled when already checked in
    first_checkin_at = serializers.DateTimeField(required=False, allow_null=True)


class GuestScanResultSerializer(serializers.Serializer):
    """Returned after scanning a complimentary (guest-list) ticket QR code."""
    success = serializers.BooleanField()
    message = serializers.CharField()
    already_checked_in = serializers.BooleanField(default=False)
    guest_name = serializers.CharField(required=False)
    event_name = serializers.CharField(required=False)
    ticket_type = serializers.CharField(required=False)
    checked_in_at = serializers.DateTimeField(required=False, allow_null=True)
    first_checkin_at = serializers.DateTimeField(required=False, allow_null=True)


class DoormanCheckinStatsSerializer(serializers.Serializer):
    """Live check-in statistics for a single event."""
    event_id = serializers.IntegerField()
    event_name = serializers.CharField()
    # Paid tickets
    paid_total = serializers.IntegerField()
    paid_checked_in = serializers.IntegerField()
    paid_pending = serializers.IntegerField()
    # Guest list
    guest_total = serializers.IntegerField()
    guest_checked_in = serializers.IntegerField()
    guest_pending = serializers.IntegerField()
    # Combined
    total_expected = serializers.IntegerField()
    total_checked_in = serializers.IntegerField()
    checkin_percentage = serializers.FloatField()
    # Recent activity (last 10 check-ins)
    recent_checkins = serializers.ListField(child=serializers.DictField())

