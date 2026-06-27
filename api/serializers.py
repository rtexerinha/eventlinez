from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from cart.models import Cart, CartItem
from customer.models import Customer
from event.models import Category, Event, Ticket as EventTicket
from order.models import Order, OrderItem
from ticket.models import Ticket
from .models import TicketShareToken


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=40)
    last_name = serializers.CharField(max_length=120)
    password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        Customer.objects.create(
            user=user,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=email,
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'email', 'cellphone']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data.get('first_name'):
            instance.first_name = user_data['first_name']
            instance.user.first_name = user_data['first_name']
        if user_data.get('last_name'):
            instance.last_name = user_data['last_name']
            instance.user.last_name = user_data['last_name']
        if validated_data.get('cellphone') is not None:
            instance.cellphone = validated_data['cellphone']
        instance.save()
        instance.user.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        validate_password(value)
        return value


# ─── Events ──────────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class EventTicketSerializer(serializers.ModelSerializer):
    qty_available = serializers.SerializerMethodField()
    sold_out = serializers.SerializerMethodField()

    class Meta:
        model = EventTicket
        fields = ['id', 'name', 'price', 'quantity', 'qty_available', 'sold_out', 'days']

    def get_qty_available(self, obj):
        try:
            return obj.qty_available()
        except Exception:
            return 0

    def get_sold_out(self, obj):
        try:
            return obj.sold_out or obj.qty_available() == 0
        except Exception:
            return False


class EventListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    city_name = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'name', 'slug', 'category', 'event_date', 'address',
            'city_name', 'image_url', 'thumbnail_url', 'is_active', 'min_price',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        try:
            url = obj.safe_image_sized_url()
            if url and request:
                return request.build_absolute_uri(url)
        except Exception:
            pass
        return None

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        try:
            url = obj.safe_thumbnail_url() if hasattr(obj, 'safe_thumbnail_url') else None
            if url and request:
                return request.build_absolute_uri(url)
        except Exception:
            pass
        return None

    def get_city_name(self, obj):
        try:
            return str(obj.city)
        except Exception:
            return ''

    def get_is_active(self, obj):
        return obj.event_date >= timezone.now()

    def get_min_price(self, obj):
        try:
            prices = [t.price for t in obj.tickets.filter(sold_out=False)]
            return float(min(prices)) if prices else None
        except Exception:
            return None


class EventDetailSerializer(EventListSerializer):
    tickets = EventTicketSerializer(many=True, read_only=True)
    description = serializers.CharField()
    qty_available = serializers.SerializerMethodField()

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + ['description', 'tickets', 'qty_available']

    def get_qty_available(self, obj):
        try:
            return obj.qty_available()
        except Exception:
            return 0


# ─── Cart ────────────────────────────────────────────────────────────────────

class CartItemSerializer(serializers.ModelSerializer):
    ticket_name = serializers.CharField(source='ticket.name', read_only=True)
    event_name = serializers.CharField(source='ticket.event.name', read_only=True)
    event_date = serializers.DateTimeField(source='ticket.event.event_date', read_only=True)
    unit_price = serializers.DecimalField(source='ticket.price', max_digits=10, decimal_places=2, read_only=True)
    subtotal = serializers.SerializerMethodField()
    fee = serializers.SerializerMethodField()
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'ticket', 'ticket_name', 'event_name', 'event_date',
            'unit_price', 'quantity', 'subtotal', 'fee', 'line_total',
        ]

    def get_subtotal(self, obj):
        return float(obj.sub_total())

    def get_fee(self, obj):
        return float(obj.fee())

    def get_line_total(self, obj):
        return float(obj.price_total())


class CartSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()
    promo_discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.SerializerMethodField()
    seconds_remaining = serializers.IntegerField(read_only=True)
    is_expired = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id', 'cart_id', 'items', 'subtotal', 'applied_promo_code',
            'promo_discount', 'total', 'seconds_remaining', 'is_expired',
        ]

    def get_items(self, obj):
        items = obj.cartitem_set.filter(active=True)
        return CartItemSerializer(items, many=True).data

    def get_subtotal(self, obj):
        return float(obj.subtotal())

    def get_total(self, obj):
        return float(obj.total_with_promo())

    def get_is_expired(self, obj):
        return obj.is_expired()


# ─── Orders ──────────────────────────────────────────────────────────────────

class OrderTicketSerializer(serializers.ModelSerializer):
    event_name = serializers.SerializerMethodField()
    event_date = serializers.SerializerMethodField()
    ticket_type = serializers.SerializerMethodField()
    qr_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['id', 'uuid', 'price', 'guest_name', 'event_name', 'event_date',
                  'ticket_type', 'checkin_date', 'qr_url']

    def get_event_name(self, obj):
        try:
            return obj.day_event.name if obj.day_event else obj.event_ticket.event.name
        except Exception:
            return ''

    def get_event_date(self, obj):
        try:
            return obj.day_event.event_date if obj.day_event else obj.event_ticket.event.event_date
        except Exception:
            return None

    def get_ticket_type(self, obj):
        try:
            return obj.event_ticket.name
        except Exception:
            return ''

    def get_qr_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/tickets/{obj.id}/qr/')
        return f'/api/tickets/{obj.id}/qr/'


class OrderItemSerializer(serializers.ModelSerializer):
    event_ticket_name = serializers.CharField(source='event_ticket.name', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'event_ticket_name', 'quantity', 'unit_price', 'amount']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    tickets = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'total', 'emailAddress', 'created', 'items', 'tickets']

    def get_tickets(self, obj):
        tickets = Ticket.objects.filter(order_item__order=obj).order_by('created_at')
        return OrderTicketSerializer(tickets, many=True, context=self.context).data


# ─── Tickets ─────────────────────────────────────────────────────────────────

class TicketSerializer(serializers.ModelSerializer):
    event_name = serializers.SerializerMethodField()
    event_date = serializers.SerializerMethodField()
    event_address = serializers.SerializerMethodField()
    event_city = serializers.SerializerMethodField()
    event_image_url = serializers.SerializerMethodField()
    ticket_type = serializers.SerializerMethodField()
    is_checked_in = serializers.SerializerMethodField()
    is_upcoming = serializers.SerializerMethodField()
    qr_url = serializers.SerializerMethodField()
    pdf_url = serializers.SerializerMethodField()
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'uuid', 'price', 'guest_name', 'created_at',
            'event_name', 'event_date', 'event_address', 'event_city', 'event_image_url',
            'ticket_type', 'day_number', 'is_checked_in', 'checkin_date',
            'is_upcoming', 'qr_url', 'pdf_url', 'share_url',
        ]

    def _event(self, obj):
        return obj.day_event if obj.day_event else (obj.event_ticket.event if obj.event_ticket else None)

    def get_event_name(self, obj):
        e = self._event(obj)
        return e.name if e else ''

    def get_event_date(self, obj):
        e = self._event(obj)
        return e.event_date if e else None

    def get_event_address(self, obj):
        e = self._event(obj)
        return e.address if e else ''

    def get_event_city(self, obj):
        e = self._event(obj)
        try:
            return str(e.city) if e else ''
        except Exception:
            return ''

    def get_event_image_url(self, obj):
        request = self.context.get('request')
        e = self._event(obj)
        if not e:
            return None
        try:
            url = e.safe_image_sized_url() if hasattr(e, 'safe_image_sized_url') else (e.image.url if e.image else None)
            if url and request:
                return request.build_absolute_uri(url)
        except Exception:
            pass
        return None

    def get_ticket_type(self, obj):
        try:
            return obj.event_ticket.name
        except Exception:
            return ''

    def get_is_checked_in(self, obj):
        return obj.checkin_date is not None

    def get_is_upcoming(self, obj):
        e = self._event(obj)
        if not e:
            return False
        return e.event_date >= timezone.now()

    def get_qr_url(self, obj):
        request = self.context.get('request')
        path = f'/api/tickets/{obj.id}/qr/'
        return request.build_absolute_uri(path) if request else path

    def get_pdf_url(self, obj):
        request = self.context.get('request')
        path = f'/api/tickets/{obj.id}/pdf/'
        return request.build_absolute_uri(path) if request else path

    def get_share_url(self, obj):
        request = self.context.get('request')
        path = f'/api/tickets/{obj.id}/share/'
        return request.build_absolute_uri(path) if request else path


class TicketShareTokenSerializer(serializers.ModelSerializer):
    share_link = serializers.SerializerMethodField()
    qr_link = serializers.SerializerMethodField()

    class Meta:
        model = TicketShareToken
        fields = ['token', 'expires_at', 'revoked', 'share_link', 'qr_link']

    def get_share_link(self, obj):
        request = self.context.get('request')
        path = f'/api/t/{obj.token}/'
        return request.build_absolute_uri(path) if request else path

    def get_qr_link(self, obj):
        request = self.context.get('request')
        path = f'/api/t/{obj.token}/qr/'
        return request.build_absolute_uri(path) if request else path


class PublicTicketSerializer(serializers.ModelSerializer):
    """Minimal read-only ticket data for share-token public endpoint."""
    event_name = serializers.SerializerMethodField()
    event_date = serializers.SerializerMethodField()
    event_address = serializers.SerializerMethodField()
    ticket_type = serializers.SerializerMethodField()
    qr_svg = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = ['id', 'uuid', 'guest_name', 'event_name', 'event_date',
                  'event_address', 'ticket_type', 'qr_svg']

    def _event(self, obj):
        return obj.day_event if obj.day_event else (obj.event_ticket.event if obj.event_ticket else None)

    def get_event_name(self, obj):
        e = self._event(obj)
        return e.name if e else ''

    def get_event_date(self, obj):
        e = self._event(obj)
        return e.event_date if e else None

    def get_event_address(self, obj):
        e = self._event(obj)
        return e.address if e else ''

    def get_ticket_type(self, obj):
        try:
            return obj.event_ticket.name
        except Exception:
            return ''

    def get_qr_svg(self, obj):
        try:
            return str(obj.as_qrcode())
        except Exception:
            return ''
