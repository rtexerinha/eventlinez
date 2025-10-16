from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from address.models import State, City, Address
from customer.models import Customer
from event.models import Category, Promoter, Event, Ticket
from promoter.models import BankAccount, Vendor, Payment
from order.models import Order, OrderItem
from cart.models import Cart, CartItem
import ticket.models as ticket_models


class Command(BaseCommand):
    help = 'Seed the database with test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete all existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write('Flushing existing data...')
            self.flush_data()

        self.stdout.write('Starting data seeding...')

        # Create data in order of dependencies
        self.create_users()
        self.create_address_data()
        self.create_categories()
        self.create_customers()
        self.create_promoters()
        self.create_vendors()
        self.create_events()
        self.create_tickets()
        self.create_orders()
        self.create_carts()

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded database with test data!')
        )

    def flush_data(self):
        """Delete existing data in reverse dependency order"""
        CartItem.objects.all().delete()
        Cart.objects.all().delete()
        ticket_models.Ticket.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Ticket.objects.all().delete()
        Event.objects.all().delete()
        Payment.objects.all().delete()
        Vendor.objects.all().delete()
        BankAccount.objects.all().delete()
        Promoter.objects.all().delete()
        Customer.objects.all().delete()
        Category.objects.all().delete()
        Address.objects.all().delete()
        City.objects.all().delete()
        State.objects.all().delete()
        # Don't delete Users as they might be needed for admin access

    def create_users(self):
        """Create test users"""
        self.stdout.write('Creating users...')

        # Admin user
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@eventlinez.com',
                password='admin123'
            )
            self.stdout.write(f'✓ Created admin user: {admin_user.username}')
        else:
            self.stdout.write('✓ Admin user already exists')

        # Txadmin superuser
        if not User.objects.filter(username='txadmin').exists():
            txadmin_user = User.objects.create_superuser(
                username='txadmin',
                email='txadmin@eventlinez.com',
                password='123456'
            )
            self.stdout.write(f'✓ Created txadmin user: {txadmin_user.username}')
        else:
            self.stdout.write('✓ Txadmin user already exists')

        # Customer users
        customer_users = [
            ('john_doe', 'john@example.com', 'John', 'Doe'),
            ('jane_smith', 'jane@example.com', 'Jane', 'Smith'),
            ('mike_wilson', 'mike@example.com', 'Mike', 'Wilson'),
            ('sarah_johnson', 'sarah@example.com', 'Sarah', 'Johnson'),
            ('david_brown', 'david@example.com', 'David', 'Brown'),
        ]

        created_customers = 0
        for username, email, first_name, last_name in customer_users:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name
                )
                created_customers += 1
                self.stdout.write(f'✓ Created customer user: {user.username}')

        self.stdout.write(f'✓ Created {created_customers} customer users')

        # Promoter users
        promoter_users = [
            ('promoter1', 'promoter1@eventlinez.com', 'Events', 'Company'),
            ('promoter2', 'promoter2@eventlinez.com', 'Music', 'Productions'),
            ('promoter3', 'promoter3@eventlinez.com', 'Sports', 'Events'),
        ]

        created_promoters = 0
        for username, email, first_name, last_name in promoter_users:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name
                )
                created_promoters += 1
                self.stdout.write(f'✓ Created promoter user: {user.username}')

        self.stdout.write(f'✓ Created {created_promoters} promoter users')

        # Show total user count
        total_users = User.objects.count()
        self.stdout.write(f'✓ Total users in database: {total_users}')

    def create_address_data(self):
        """Create states, cities and addresses"""
        self.stdout.write('Creating address data...')

        states_data = [
            'California',
            'New York',
            'Texas',
            'Florida',
            'Illinois',
            'Pennsylvania'
        ]

        states = []
        for state_name in states_data:
            state, created = State.objects.get_or_create(name=state_name)
            states.append(state)

        cities_data = [
            ('Los Angeles', 'California'),
            ('San Francisco', 'California'),
            ('New York', 'New York'),
            ('Buffalo', 'New York'),
            ('Houston', 'Texas'),
            ('Dallas', 'Texas'),
            ('Miami', 'Florida'),
            ('Orlando', 'Florida'),
            ('Chicago', 'Illinois'),
            ('Philadelphia', 'Pennsylvania'),
        ]

        for city_name, state_name in cities_data:
            state = State.objects.get(name=state_name)
            City.objects.get_or_create(name=city_name, state=state)

    def create_categories(self):
        """Create event categories"""
        self.stdout.write('Creating categories...')

        categories = [
            'Music',
            'Sports',
            'Theater',
            'Comedy',
            'Business',
            'Food & Drink',
            'Arts & Culture',
            'Technology',
            'Health & Wellness',
            'Fashion'
        ]

        for cat_name in categories:
            Category.objects.get_or_create(
                name=cat_name,
                defaults={'slug': cat_name.lower().replace(' ', '-').replace('&', 'and')}
            )

    def create_customers(self):
        """Create customer profiles"""
        self.stdout.write('Creating customers...')

        customer_users = User.objects.filter(username__in=[
            'john_doe', 'jane_smith', 'mike_wilson', 'sarah_johnson', 'david_brown'
        ])

        self.stdout.write(f'Found {customer_users.count()} customer users to process')

        addresses = [
            '123 Main St, Los Angeles, CA 90210',
            '456 Oak Ave, New York, NY 10001',
            '789 Pine St, Houston, TX 77001',
            '321 Elm Dr, Miami, FL 33101',
            '654 Maple Ln, Chicago, IL 60601',
        ]

        created_customers = 0
        for i, user in enumerate(customer_users):
            try:
                # Check if customer profile already exists
                existing_customer = Customer.objects.filter(user=user).first()
                if not existing_customer:
                    customer = Customer.objects.create(
                        user=user,
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                        address=addresses[i % len(addresses)],
                        city='CA',
                        zip=f'{90210 + i}',
                        cellphone=f'+1555010{100 + i}',
                        terms_confirmed=True
                    )
                    created_customers += 1
                    self.stdout.write(f'✓ Created customer profile for: {user.username}')
                else:
                    self.stdout.write(f'✓ Customer profile already exists for: {user.username}')
            except Exception as e:
                self.stdout.write(f'✗ Error creating customer for {user.username}: {e}')

        self.stdout.write(f'✓ Created {created_customers} customer profiles')

        # Show total customer count
        total_customers = Customer.objects.count()
        self.stdout.write(f'✓ Total customers in database: {total_customers}')

    def create_promoters(self):
        """Create promoter profiles and bank accounts"""
        self.stdout.write('Creating promoters...')

        promoter_users = User.objects.filter(username__startswith='promoter')

        promoter_data = [
            ('Events Company LLC', 'promoter1@eventlinez.com', '123456789', '+15550101', 
             '123 Business St', 'Los Angeles', '90210', 'ACC123456789', 'Bank of America', 'RT123456789'),
            ('Music Productions Inc', 'promoter2@eventlinez.com', '987654321', '+15550102', 
             '456 Music Ave', 'New York', '10001', 'ACC987654321', 'Chase Bank', 'RT987654321'),
            ('Sports Events Corp', 'promoter3@eventlinez.com', '456789123', '+15550103', 
             '789 Sports Blvd', 'Houston', '77001', 'ACC456789123', 'Wells Fargo', 'RT456789123'),
        ]

        for i, user in enumerate(promoter_users):
            if not hasattr(user, 'promoter') and i < len(promoter_data):
                data = promoter_data[i]
                promoter = Promoter.objects.create(
                    name=data[0],
                    email=data[1],
                    user=user,
                    ssn=data[2],
                    phone=data[3],
                    address=data[4],
                    city=data[5],
                    zip=data[6],
                    account_id=f'acct_{i+1}',
                )

                # Create bank account
                BankAccount.objects.create(
                    promoter=promoter,
                    account_number=data[7],
                    bank_name=data[8],
                    routing_number=data[9]
                )

    def create_vendors(self):
        """Create vendors for promoters"""
        self.stdout.write('Creating vendors...')

        promoters = Promoter.objects.all()
        if not promoters:
            self.stdout.write('No promoters found, skipping vendors...')
            return

        vendor_data = [
            ('Alice', 'Johnson', 'alice@example.com', '+15550201'),
            ('Bob', 'Smith', 'bob@example.com', '+15550202'),
            ('Carol', 'Williams', 'carol@example.com', '+15550203'),
            ('Dan', 'Brown', 'dan@example.com', '+15550204'),
            ('Eva', 'Davis', 'eva@example.com', '+15550205'),
            ('Frank', 'Miller', 'frank@example.com', '+15550206'),
        ]

        for i, (first_name, last_name, email, phone) in enumerate(vendor_data):
            promoter = promoters[i % len(promoters)]
            Vendor.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'phone': phone,
                    'promoter': promoter,
                }
            )

    def create_events(self):
        """Create sample events"""
        self.stdout.write('Creating events...')

        categories = Category.objects.all()
        cities = City.objects.all()
        promoters = Promoter.objects.all()

        if not categories or not cities or not promoters:
            self.stdout.write('Missing required data for events, skipping...')
            return

        events_data = [
            ('Summer Music Festival 2024', 'Join us for an amazing summer music festival featuring top artists!', 
             'music', '123 Festival Grounds', 30),
            ('Tech Conference 2024', 'The biggest technology conference of the year with industry leaders.',
             'technology', '456 Convention Center', 15),
            ('Comedy Night Live', 'Laugh out loud with our fantastic lineup of comedians!',
             'comedy', '789 Comedy Club', 7),
            ('Food & Wine Expo', 'Taste the best food and wine from local restaurants and wineries.',
             'food-and-drink', '321 Expo Center', 45),
            ('Basketball Championship', 'Finals of the local basketball championship tournament.',
             'sports', '654 Sports Arena', 2),
            ('Art Gallery Opening', 'Grand opening of our new contemporary art gallery exhibition.',
             'arts-and-culture', '987 Art District', 60),
            ('Business Networking Event', 'Connect with professionals and grow your business network.',
             'business', '147 Business Tower', 20),
            ('Fashion Week Finale', 'The grand finale of fashion week with top designers.',
             'fashion', '258 Fashion District', 5),
        ]

        for name, description, cat_slug, address, days_ahead in events_data:
            category = categories.filter(slug=cat_slug).first() or categories.first()
            city = random.choice(cities)
            promoter = random.choice(promoters)
            event_date = timezone.now() + timedelta(days=days_ahead)

            event, created = Event.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'description': description,
                    'event_date': event_date,
                    'address': address,
                    'city': city,
                    'promoter': promoter,
                    'available': True,
                }
            )

    def create_tickets(self):
        """Create tickets for events"""
        self.stdout.write('Creating tickets...')

        events = Event.objects.all()
        if not events:
            self.stdout.write('No events found, skipping tickets...')
            return

        ticket_types = [
            ('General Admission', Decimal('25.00'), 100),
            ('VIP', Decimal('75.00'), 50),
            ('Premium', Decimal('150.00'), 25),
            ('Student Discount', Decimal('15.00'), 75),
            ('Early Bird', Decimal('20.00'), 200),
        ]

        for event in events:
            # Create 2-3 different ticket types per event
            num_tickets = random.randint(2, 4)
            selected_tickets = random.sample(ticket_types, min(num_tickets, len(ticket_types)))

            for name, price, quantity in selected_tickets:
                Ticket.objects.get_or_create(
                    name=name,
                    event=event,
                    defaults={
                        'price': price,
                        'quantity': quantity,
                        'sold_out': False,
                    }
                )

    def create_orders(self):
        """Create sample orders with sold tickets"""
        self.stdout.write('Creating orders...')

        customers = Customer.objects.all()
        tickets = Ticket.objects.all()
        vendors = Vendor.objects.all()

        if not customers or not tickets:
            self.stdout.write('Missing required data for orders, skipping...')
            return

        # Create 10 sample orders
        for i in range(10):
            customer = random.choice(customers)

            order = Order.objects.create(
                token=f'order_token_{i+1}',
                total=Decimal('0.00'),
                emailAddress=customer.email,
                billingName=f'{customer.first_name} {customer.last_name}',
                billingAddress1=customer.address,
                billingCity=customer.city,
                billingPostcode=customer.zip,
                billingCountry='USA',
                shippingName=f'{customer.first_name} {customer.last_name}',
                shippingAddress1=customer.address,
                shippingCity=customer.city,
                shippingPostcode=customer.zip,
                shippingCountry='USA',
                payment_code=f'pay_{i+1}',
                customer=customer
            )

            # Add 1-3 ticket types to each order
            order_total = Decimal('0.00')
            num_items = random.randint(1, 3)

            for _ in range(num_items):
                ticket = random.choice(tickets)
                quantity = random.randint(1, 3)
                vendor = random.choice(vendors) if vendors and random.choice([True, False]) else None

                # Calculate fees
                unit_price = ticket.price
                fee_per_ticket = unit_price * Decimal('0.12')  # EVENTLINEZ_FEE
                total_fee = fee_per_ticket * quantity
                amount = (unit_price * quantity) + total_fee

                order_item = OrderItem.objects.create(
                    order=order,
                    event_ticket=ticket,
                    quantity=quantity,
                    unit_price=unit_price,
                    fee=total_fee,
                    amount=amount,
                    vendor=vendor
                )

                order_total += amount

            # Update order total
            order.total = order_total
            order.save()

    def create_carts(self):
        """Create sample cart data"""
        self.stdout.write('Creating carts...')

        tickets = Ticket.objects.all()
        vendors = Vendor.objects.all()

        if not tickets:
            self.stdout.write('No tickets found, skipping carts...')
            return

        # Create 5 sample carts
        for i in range(5):
            cart = Cart.objects.create(
                cart_id=f'cart_{i+1}_{random.randint(1000, 9999)}'
            )

            # Add 1-2 items to each cart
            num_items = random.randint(1, 2)

            for _ in range(num_items):
                ticket = random.choice(tickets)
                quantity = random.randint(1, 2)
                vendor = random.choice(vendors) if vendors and random.choice([True, False]) else None

                CartItem.objects.create(
                    ticket=ticket,
                    cart=cart,
                    quantity=quantity,
                    vendor=vendor,
                    active=True
                )

        self.stdout.write('Sample carts created successfully!')
