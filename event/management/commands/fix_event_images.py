from django.core.management.base import BaseCommand
from django.core.files import File
from event.models import Event
from PIL import Image
import io
import random
import os


class Command(BaseCommand):
    help = 'Fix missing event images by creating placeholder images'

    def handle(self, *args, **options):
        self.stdout.write('🖼️ FIXING EVENT IMAGES')
        self.stdout.write('=' * 50)

        events_without_images = []
        events_with_broken_images = []

        for event in Event.objects.all():
            if not event.image:
                events_without_images.append(event)
            else:
                # Check if image file exists
                try:
                    event.image.open()
                    event.image.close()
                except (FileNotFoundError, IOError):
                    events_with_broken_images.append(event)

        self.stdout.write(f'Found {len(events_without_images)} events without images')
        self.stdout.write(f'Found {len(events_with_broken_images)} events with broken images')

        # Fix events without images
        for i, event in enumerate(events_without_images):
            self._create_placeholder_image(event, i)
            self.stdout.write(f'✅ Created image for: {event.name}')

        # Fix events with broken images  
        for i, event in enumerate(events_with_broken_images):
            self._create_placeholder_image(event, i + len(events_without_images))
            self.stdout.write(f'🔧 Fixed broken image for: {event.name}')

        total_fixed = len(events_without_images) + len(events_with_broken_images)
        self.stdout.write(f'\n✅ Fixed {total_fixed} event images!')

    def _create_placeholder_image(self, event, index):
        """Create a placeholder image for an event"""
        # Create colorful placeholder
        colors = [
            (255, 99, 132),   # Pink
            (54, 162, 235),   # Blue  
            (255, 205, 86),   # Yellow
            (75, 192, 192),   # Teal
            (153, 102, 255),  # Purple
            (255, 159, 64),   # Orange
        ]

        color = colors[index % len(colors)]

        # Create image
        img = Image.new('RGB', (800, 400), color=color)

        # Add text (optional - requires PIL with text support)
        try:
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)

            # Try to use a default font
            try:
                font = ImageFont.truetype("Arial.ttf", 24)
            except:
                font = ImageFont.load_default()

            # Add event name
            text = event.name[:30] + "..." if len(event.name) > 30 else event.name
            draw.text((50, 180), text, fill=(255, 255, 255), font=font)

        except ImportError:
            # If PIL text features not available, just use solid color
            pass

        # Save to BytesIO
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=85)
        img_io.seek(0)

        # Create unique filename
        from django.utils import timezone
        filename = f'event_{event.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.jpg'

        # Save to event
        event.image.save(filename, File(img_io), save=True)
