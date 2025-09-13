from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from event.models import Event, Category, Promoter
from address.models import City
import random


class Command(BaseCommand):
    help = 'Seed events with test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing events before seeding',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of events to create (default: 5)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing events...')
            Event.objects.all().delete()

        # Get or create organizer - ENSURE calisamba@gmail.com is the owner
        try:
            # Try to get existing user
            try:
                organizer_user = User.objects.get(username='calisamba@gmail.com')
            except User.DoesNotExist:
                # Create the user if it doesn't exist
                self.stdout.write('Creating user calisamba@gmail.com')
                organizer_user = User.objects.create_user(
                    username='calisamba@gmail.com',
                    email='calisamba@gmail.com',
                    password='password123',
                    first_name='Cali',
                    last_name='Samba'
                )

            # Try to get existing promoter
            try:
                promoter = Promoter.objects.get(user=organizer_user)
            except Promoter.DoesNotExist:
                # Create the promoter if it doesn't exist
                self.stdout.write('Creating promoter for calisamba@gmail.com')
                promoter = Promoter.objects.create(
                    user=organizer_user,
                    name='Cali Samba Promotions',
                    description='Official promoter for testing',
                    website='https://example.com',
                    email='calisamba@gmail.com'
                )

            self.stdout.write(f'Using promoter: {promoter.name} ({organizer_user.username})')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up organizer: {e}')
            )
            return

        # Get or create a default city with proper State relationship
        from address.models import State

        # Create California state first
        california, created = State.objects.get_or_create(name='California')
        if created:
            self.stdout.write('Created California state')

        # Create Los Angeles city
        city, created = City.objects.get_or_create(
            name='Los Angeles',
            defaults={'state': california}
        )
        if created:
            self.stdout.write('Created Los Angeles city')

        # Create categories if they don't exist
        categories = [
            {'name': 'Music'},
            {'name': 'Sports'},
            {'name': 'Business'},
            {'name': 'Food'},
            {'name': 'Technology'},
        ]

        for cat_data in categories:
            from django.template.defaultfilters import slugify
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'slug': slugify(cat_data['name'])}
            )

        # Sample event data
        sample_events = [
            {
                'name': 'Summer Music Festival 2025',
                'description': 'Join us for the biggest summer music festival featuring top artists from around the world. Experience amazing performances, food, and entertainment.',
                'category': 'Music',
                'address': 'Central Park, New York',
            },
            {
                'name': 'Tech Innovation Conference',
                'description': 'Discover the latest trends in technology and innovation. Network with industry leaders and attend workshops on cutting-edge technologies.',
                'category': 'Technology',
                'address': 'Convention Center, San Francisco',
            },
            {
                'name': 'Food & Wine Expo',
                'description': 'Taste exquisite dishes from renowned chefs and sample wines from top vineyards. A culinary experience you won\'t forget.',
                'category': 'Food',
                'address': 'Downtown Exhibition Hall, Chicago',
            },
            {
                'name': 'Basketball Championship Finals',
                'description': 'Watch the most exciting basketball finals of the season. Cheer for your favorite team in this thrilling championship match.',
                'category': 'Sports',
                'address': 'Sports Arena, Los Angeles',
            },
            {
                'name': 'Startup Networking Summit',
                'description': 'Connect with entrepreneurs, investors, and startup founders. Learn from success stories and pitch your ideas to potential investors.',
                'category': 'Business',
                'address': 'Business District, Austin',
            },
        ]

        count = min(options['count'], len(sample_events))

        with transaction.atomic():
            for i in range(count):
                event_data = sample_events[i]

                # Generate random future date
                event_date = timezone.now() + timedelta(days=random.randint(30, 180))

                category = Category.objects.get(name=event_data['category'])

                # Create a simple image placeholder that actually gets saved
                from django.core.files.base import ContentFile
                from PIL import Image
                import io

                # Create a simple placeholder image with different colors
                colors = ['blue', 'green', 'red', 'purple', 'orange']
                color = colors[i % len(colors)]

                img = Image.new('RGB', (800, 400), color=color)
                img_io = io.BytesIO()
                img.save(img_io, format='JPEG', quality=85)

                # Ensure media directory exists
                import os
                from django.conf import settings
                media_dir = os.path.join(settings.MEDIA_ROOT, 'event')
                os.makedirs(media_dir, exist_ok=True)

                img_content = ContentFile(img_io.getvalue(), name=f'event_{i+1}.jpg')

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
                        'image': img_content,
                    }
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Created event: {event.name}')
                    )
                else:
                    self.stdout.write(f'Event already exists: {event.name}')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded {count} events!')
        )

        # Verify all events belong to calisamba@gmail.com
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('VERIFYING EVENT OWNERSHIP:')
        all_events = Event.objects.all()
        for event in all_events:
            owner_email = event.promoter.user.username
            if owner_email == 'calisamba@gmail.com':
                self.stdout.write(f'✅ {event.name} -> {owner_email}')
            else:
                self.stdout.write(f'❌ {event.name} -> {owner_email} (SHOULD BE calisamba@gmail.com)')

        # Count events owned by calisamba@gmail.com
        correct_owner_count = all_events.filter(promoter__user__username='calisamba@gmail.com').count()
        self.stdout.write(f'\nSUMMARY: {correct_owner_count}/{all_events.count()} events belong to calisamba@gmail.com')
