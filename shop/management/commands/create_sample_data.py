from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import BusinessPartner
from event.models import Event


class Command(BaseCommand):
    help = 'Create sample business partners and gallery data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample business partners...')
        
        # Create sample business partners
        partners_data = [
            {
                'name': 'EventPro Solutions',
                'description': 'Professional event management and planning services',
                'website': 'https://eventpro.example.com',
                'email': 'contact@eventpro.example.com',
                'phone': '+1 (555) 123-4567',
                'display_order': 1
            },
            {
                'name': 'Audio Visual Tech',
                'description': 'High-quality sound and lighting equipment rental',
                'website': 'https://avtech.example.com',
                'email': 'info@avtech.example.com',
                'phone': '+1 (555) 234-5678',
                'display_order': 2
            },
            {
                'name': 'Catering Masters',
                'description': 'Premium catering services for all types of events',
                'website': 'https://cateringmasters.example.com',
                'email': 'bookings@cateringmasters.example.com',
                'phone': '+1 (555) 345-6789',
                'display_order': 3
            },
            {
                'name': 'Security Plus',
                'description': 'Professional event security and crowd management',
                'website': 'https://securityplus.example.com',
                'email': 'security@securityplus.example.com',
                'phone': '+1 (555) 456-7890',
                'display_order': 4
            },
            {
                'name': 'Photo & Video Pro',
                'description': 'Professional photography and videography services',
                'website': 'https://photovideo.example.com',
                'email': 'bookings@photovideo.example.com',
                'phone': '+1 (555) 567-8901',
                'display_order': 5
            },
            {
                'name': 'Venue Experts',
                'description': 'Unique venues for memorable events',
                'website': 'https://venueexperts.example.com',
                'email': 'venues@venueexperts.example.com',
                'phone': '+1 (555) 678-9012',
                'display_order': 6
            }
        ]
        
        created_count = 0
        for partner_data in partners_data:
            partner, created = BusinessPartner.objects.get_or_create(
                name=partner_data['name'],
                defaults=partner_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created partner: {partner.name}')
            else:
                self.stdout.write(f'  - Partner already exists: {partner.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} business partners')
        )
        
        # Note about gallery photos
        self.stdout.write('\n' + '='*50)
        self.stdout.write('📷 GALLERY SETUP COMPLETE!')
        self.stdout.write('='*50)
        self.stdout.write('\nTo add gallery photos:')
        self.stdout.write('1. Go to: http://localhost:8000/admin/shop/eventgallery/')
        self.stdout.write('2. Click "📷 Bulk Upload Photos" button')
        self.stdout.write('3. Drag and drop multiple images at once')
        self.stdout.write('4. Images will be automatically optimized and thumbnails generated')
        self.stdout.write('\nFeatures available:')
        self.stdout.write('• Drag and drop support')
        self.stdout.write('• Multiple image selection')
        self.stdout.write('• Automatic image optimization (resize to 1920x1080, 85% quality)')
        self.stdout.write('• Automatic thumbnail generation (300x300)')
        self.stdout.write('• File validation (type, size, dimensions)')
        self.stdout.write('• Preview before upload')
        self.stdout.write('• Bulk title and description assignment')
        self.stdout.write('\nBusiness partners will now appear on the main page!')
        self.stdout.write('Gallery photos (when uploaded) will appear in the gallery section.')
