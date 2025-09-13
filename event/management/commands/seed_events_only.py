from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from event.models import Event, Category, Promoter
from address.models import City
import random


class Command(BaseCommand):
    help = 'Seed only events (assumes users already exist)'

    def handle(self, *args, **options):
        self.stdout.write('🎉 SEEDING EVENTS ONLY')
        self.stdout.write('=' * 50)

        # Get or create organizer
        try:
            organizer_user = User.objects.get(username='calisamba@gmail.com')
            promoter = Promoter.objects.get(user=organizer_user)
            self.stdout.write(f'✅ Using promoter: {promoter.name} ({organizer_user.username})')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ User calisamba@gmail.com not found. Run: make seed-users')
            )
            return
        except Promoter.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('❌ Promoter profile not found. Run: make seed-users')
            )
            return

        # Get or create a default city
        city, created = City.objects.get_or_create(
            name='New York',
            defaults={'country': 'US', 'state': 'NY'}
        )
        if created:
            self.stdout.write(f'✅ Created city: {city.name}')

        # Create categories if they don't exist
        categories = ['Music', 'Sports', 'Business', 'Food', 'Technology']

        self.stdout.write('📋 Creating categories...')
        for cat_name in categories:
            from django.template.defaultfilters import slugify
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'slug': slugify(cat_name)}
            )
            if created:
                self.stdout.write(f'  ✅ Created category: {cat_name}')
            else:
                self.stdout.write(f'  ➡️  Category exists: {cat_name}')

        # Sample event data
        sample_events = [
            {
                'name': 'Summer Music Festival 2025',
                'description': 'Join us for the biggest summer music festival featuring top artists from around the world.',
                'category': 'Music',
                'address': 'Central Park, New York',
            },
            {
                'name': 'Tech Innovation Conference',
                'description': 'Discover the latest trends in technology and innovation.',
                'category': 'Technology',
                'address': 'Convention Center, San Francisco',
            },
            {
                'name': 'Food & Wine Expo',
                'description': 'Taste exquisite dishes from renowned chefs.',
                'category': 'Food',
                'address': 'Downtown Exhibition Hall, Chicago',
            },
        ]

        self.stdout.write('🎪 Creating events...')
        with transaction.atomic():
            for i, event_data in enumerate(sample_events):
                # Generate random future date
                event_date = timezone.now() + timedelta(days=random.randint(30, 180))

                category = Category.objects.get(name=event_data['category'])

                # Create a simple placeholder image
                import tempfile
                from django.core.files import File
                from PIL import Image
                import io

                img = Image.new('RGB', (800, 400), color='blue')
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG')
                img_io.seek(0)
                img_file = File(img_io, name=f'event_{i+1}.jpg')

                event, created = Event.objects.get_or_create(
                    name=event_data['name'],
                    defaults={
                        'description': event_data['description'],
                        'category': category,
                        'event_date': event_date,
                        'address': event_data['address'],
                        'city': city,
                        'promoter': promoter,
                        'available': True,
                        'image': img_file,
                    }
                )

                if created:
                    self.stdout.write(f'  ✅ Created event: {event.name}')
                else:
                    self.stdout.write(f'  ➡️  Event exists: {event.name}')

        # Verify results
        total_events = Event.objects.count()
        promoter_events = Event.objects.filter(promoter=promoter).count()

        self.stdout.write(f'\n📊 RESULTS:')
        self.stdout.write(f'  Total events in database: {total_events}')
        self.stdout.write(f'  Events for {promoter.name}: {promoter_events}')

        if promoter_events > 0:
            self.stdout.write('✅ Events created successfully!')
        else:
            self.stdout.write('❌ No events created for promoter')
