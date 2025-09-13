from django.core.management.base import BaseCommand
from django.conf import settings
from event.models import Event
import os


class Command(BaseCommand):
    help = 'Check media file configuration and event images'

    def handle(self, *args, **options):
        self.stdout.write('📁 MEDIA CONFIGURATION CHECK')
        self.stdout.write('=' * 50)

        # Show media settings
        self.stdout.write('Media Settings:')
        self.stdout.write(f'  MEDIA_URL: {settings.MEDIA_URL}')
        self.stdout.write(f'  MEDIA_ROOT: {settings.MEDIA_ROOT}')

        # Check if media directory exists
        if os.path.exists(settings.MEDIA_ROOT):
            self.stdout.write(f'✅ MEDIA_ROOT directory exists')
        else:
            self.stdout.write(f'❌ MEDIA_ROOT directory does not exist')

        # Check event images
        events = Event.objects.all()
        self.stdout.write(f'\n📊 Checking {events.count()} events:')

        for event in events[:5]:  # Check first 5 events
            if event.image:
                self.stdout.write(f'\nEvent: {event.name}')
                self.stdout.write(f'  Image field: {event.image.name}')
                self.stdout.write(f'  Expected path: {event.image.path}')

                # Check if file exists
                try:
                    if os.path.exists(event.image.path):
                        size = os.path.getsize(event.image.path)
                        self.stdout.write(f'  ✅ File exists ({size} bytes)')
                    else:
                        self.stdout.write(f'  ❌ File not found at: {event.image.path}')
                except:
                    self.stdout.write(f'  ❌ Error accessing file')

                # Check URL access
                self.stdout.write(f'  URL: {event.image.url}')
            else:
                self.stdout.write(f'{event.name}: No image')

        # Check Docker vs local paths
        self.stdout.write(f'\n🐳 ENVIRONMENT CHECK:')
        current_path = os.getcwd()
        self.stdout.write(f'Current working directory: {current_path}')

        if '/app' in current_path:
            self.stdout.write('✅ Running inside Docker container')
        else:
            self.stdout.write('⚠️ Running locally (not in Docker)')
            self.stdout.write('This might cause media file path issues')
