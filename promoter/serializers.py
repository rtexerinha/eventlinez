from rest_framework import serializers
from django.contrib.auth.models import User
from event.models import Promoter, Event, Category, Ticket
from address.models import City


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


class EventSerializers(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    address = serializers.CharField()
    available = serializers.BooleanField(default=False)
    image = serializers.ImageField()
    category = serializers.CharField()
    event_date = serializers.DateTimeField()
    city = serializers.CharField()
    id = serializers.IntegerField(read_only=True)
    qty_available = serializers.SerializerMethodField(read_only=True)
    qty_sould = serializers.SerializerMethodField(read_only=True)
    quantity = serializers.SerializerMethodField(read_only=True)
    amount = serializers.SerializerMethodField(read_only=True)
    url = serializers.SerializerMethodField(read_only=True)

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


class TicketSerializers(serializers.Serializer):
    name = serializers.CharField(max_length=80)
    event = serializers.CharField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        model = Ticket
        fields = '__all__'

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

        instance.save()

        return instance
