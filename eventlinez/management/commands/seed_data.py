from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from event.models import Event, TicketType
from shop.models import EventGallery
from promoter.models import Promoter
from customer.models import Customer
from address.models import State, City, Address
import random


class Command(BaseCommand):
    help = 'Seed the database with test data for the test environment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force seeding even if data already exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Starting database seeding...'))

        # Check if we should force seeding or if database is empty
        if not options['force'] and Event.objects.exists():
            self.stdout.write(
                self.style.WARNING('Database already contains data. Use --force to override.')
            )
            return

        # Create superuser
        self.create_admin_user()
        
        # Create states and cities
        self.create_locations()
        
        # Create promoters
        promoters = self.create_promoters()
        
        # Create customers
        customers = self.create_customers()
        
        # Create events with tickets
        events = self.create_events(promoters)
        
        # Create event galleries
        self.create_event_galleries(events)

        self.stdout.write(
            self.style.SUCCESS('✅ Database seeding completed successfully!')
        )

    def create_admin_user(self):
        """Create admin user for testing"""
        self.stdout.write('👤 Creating admin user...')
        
        if User.objects.filter(username='admin').exists():
            User.objects.filter(username='admin').delete()
            
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@eventlinez.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        
        self.stdout.write(f'✅ Created admin user: {admin_user.username}')

    def create_locations(self):
        """Create test states and cities"""
        self.stdout.write('🌎 Creating locations...')
        
        # Create states
        states_data = [
            ('California', 'CA'),
            ('Texas', 'TX'),
            ('New York', 'NY'),
            ('Florida', 'FL'),
        ]
        
        for name, code in states_data:
            state, created = State.objects.get_or_create(
                name=name,
                defaults={'code': code}
            )
            if created:
                self.stdout.write(f'  📍 Created state: {name}')

        # Create cities
        ca_state = State.objects.get(code='CA')
        cities_data = [
            ('Los Angeles', ca_state),
            ('San Francisco', ca_state),
            ('San Diego', ca_state),
        ]
        
        for name, state in cities_data:
            city, created = City.objects.get_or_create(
                name=name,
                state=state
            )
            if created:
                self.stdout.write(f'  🏙️ Created city: {name}')

    def create_promoters(self):
        """Create test promoters"""
        self.stdout.write('🎭 Creating promoters...')
        
        promoters_data = [
            {
                'name': 'EventCorp',
                'email': 'contact@eventcorp.com',
                'phone': '555-0101',
                'description': 'Professional event management company'
            },
            {
                'name': 'Party Masters',
                'email': 'info@partymasters.com', 
                'phone': '555-0102',
                'description': 'Specializing in entertainment events'
            },
            {
                'name': 'Corporate Events Inc',
                'email': 'hello@corporateevents.com',
                'phone': '555-0103', 
                'description': 'Business and corporate event specialists'
            }
        ]
        
        promoters = []
        for data in promoters_data:
            # Create user for promoter
            user = User.objects.create_user(
                username=data['email'],
                email=data['email'],
                password='promoter123',
                first_name=data['name'].split()[0],
                last_name=data['name'].split()[-1] if ' ' in data['name'] else 'Inc'
            )
            
            promoter = Promoter.objects.create(
                user=user,
                name=data['name'],
                email=data['email'],
                phone=data['phone'],
                description=data['description']
            )
            promoters.append(promoter)
            self.stdout.write(f'  🎪 Created promoter: {promoter.name}')
            
        return promoters

    def create_customers(self):
        """Create test customers"""
        self.stdout.write('👥 Creating customers...')
        
        customers_data = [
            {
                'username': 'john.doe',
                'email': 'john@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '555-1001'
            },
            {
                'username': 'jane.smith',
                'email': 'jane@example.com',
                'first_name': 'Jane', 
                'last_name': 'Smith',
                'phone': '555-1002'
            },
            {
                'username': 'mike.wilson',
                'email': 'mike@example.com',
                'first_name': 'Mike',
                'last_name': 'Wilson', 
                'phone': '555-1003'
            }
        ]
        
        customers = []
        for data in customers_data:
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                email=data['email'],
                password='customer123',
                first_name=data['first_name'],
                last_name=data['last_name']
            )
            
            # Create customer
            customer = Customer.objects.create(
                user=user,
                phone=data['phone'],
                terms_confirmed=True
            )
            customers.append(customer)
            self.stdout.write(f'  👤 Created customer: {customer.user.get_full_name()}')
            
        return customers

    def create_events(self, promoters):
        """Create test events with tickets"""
        self.stdout.write('🎉 Creating events...')
        
        # Get a city for events
        city = City.objects.first()
        
        events_data = [
            {
                'name': 'Summer Music Festival 2025',
                'description': 'Join us for the biggest music festival of the year featuring top artists from around the world.',
                'category': 'music',
                'days_ahead': 30,
                'price_range': (50, 150)
            },
            {
                'name': 'Tech Conference 2025',
                'description': 'Learn about the latest in technology and network with industry professionals.',
                'category': 'conference',
                'days_ahead': 45,
                'price_range': (100, 300)
            },
            {
                'name': 'Food & Wine Festival',
                'description': 'Taste amazing dishes and wines from local restaurants and wineries.',
                'category': 'food',
                'days_ahead': 20,
                'price_range': (75, 200)
            },
            {
                'name': 'Art Gallery Opening',
                'description': 'Exclusive preview of contemporary art from emerging artists.',
                'category': 'art',
                'days_ahead': 15,
                'price_range': (25, 75)
            },
            {
                'name': 'Comedy Night Live',
                'description': 'Laugh out loud with the best comedians in the city.',
                'category': 'comedy',
                'days_ahead': 10,
                'price_range': (30, 60)
            },
            {
                'name': 'Business Networking Mixer',
                'description': 'Connect with business professionals and entrepreneurs.',
                'category': 'networking',
                'days_ahead': 7,
                'price_range': (40, 80)
            }
        ]
        
        events = []
        for i, data in enumerate(events_data):
            event_date = timezone.now() + timedelta(days=data['days_ahead'])
            promoter = promoters[i % len(promoters)]
            
            event = Event.objects.create(
                name=data['name'],
                description=data['description'],
                event_date=event_date,
                promoter=promoter,
                city=city,
                address_line_1=f'{random.randint(100, 9999)} Main Street',
                zipcode=f'{random.randint(10000, 99999)}',
                is_active=True,
                category=data['category']
            )
            
            # Create ticket types for each event
            ticket_types_data = [
                {'name': 'General Admission', 'price': data['price_range'][0], 'quantity': 100},
                {'name': 'VIP', 'price': data['price_range'][1], 'quantity': 25},
            ]
            
            for ticket_data in ticket_types_data:
                TicketType.objects.create(
                    event=event,
                    name=ticket_data['name'],
                    price=ticket_data['price'],
                    quantity_available=ticket_data['quantity'],
                    quantity_total=ticket_data['quantity'],
                    is_active=True
                )
            
            events.append(event)
            self.stdout.write(f'  🎫 Created event: {event.name}')
            
        return events

    def create_event_galleries(self, events):
        """Create test event gallery entries (without actual images)"""
        self.stdout.write('📸 Creating event galleries...')
        
        # Create some gallery entries for events (without actual image files)
        for event in events[:3]:  # Only for first 3 events
            for i in range(random.randint(2, 4)):
                gallery = EventGallery.objects.create(
                    event=event,
                    title=f'{event.name} - Photo {i+1}',
                    description=f'Great moment from {event.name}'
                    # Note: Not setting image field to avoid file issues
                )
                self.stdout.write(f'  📷 Created gallery item for: {event.name}')
