import base64

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from rest_framework import serializers

from address.models import City
from event.models import Promoter, Event, Category, Ticket
from promoter.models import Partner


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
    sold_out = serializers.BooleanField(default=False, required=False)

    class Meta:
        model = Ticket
        fields = '__all__'

    def create(self, validated_data):
        validated_data['sold_out'] = False

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
            raise serializers.ValidationError('User not Found')

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

