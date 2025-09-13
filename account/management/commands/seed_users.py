from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from customer.models import Customer
from event.models import Promoter


class Command(BaseCommand):
    help = 'Seed users with default test accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing users before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            # Delete in the correct order to avoid foreign key constraints
            from ticket.models import Ticket
            from order.models import OrderItem, Order
            from event.models import Event, Ticket as EventTicket, Category

            # Delete tickets first
            Ticket.objects.all().delete()
            self.stdout.write('Deleted tickets')

            # Delete orders and order items
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            self.stdout.write('Deleted orders')

            # Delete event tickets and events
            EventTicket.objects.all().delete()
            Event.objects.all().delete()
            self.stdout.write('Deleted events')

            # Delete categories
            Category.objects.all().delete()
            self.stdout.write('Deleted categories')

            # Delete promoter and customer profiles
            Promoter.objects.all().delete()
            Customer.objects.all().delete()
            self.stdout.write('Deleted promoter and customer profiles')

            # Finally delete users (excluding superusers)
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write('Deleted users')

        with transaction.atomic():
            # Create organizer user
            organizer_user, created = User.objects.get_or_create(
                username='calisamba@gmail.com',
                email='calisamba@gmail.com',
                defaults={
                    'first_name': 'Calisa',
                    'last_name': 'Mbaa',
                    'is_staff': False,
                    'is_active': True,
                }
            )
            if created:
                organizer_user.set_password('123456')
                organizer_user.save()

            # Create promoter profile for organizer
            promoter, created = Promoter.objects.get_or_create(
                user=organizer_user,
                defaults={
                    'name': 'Calisa Mbaa Events',
                    'email': 'calisamba@gmail.com',
                    'phone': '+1234567890',
                    'address': '123 Event Street',
                    'city': 'New York',
                    'zip': '10001'
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created organizer user: {organizer_user.username}')
                )
            else:
                self.stdout.write(f'Organizer user already exists: {organizer_user.username}')

            # Create regular user
            regular_user, created = User.objects.get_or_create(
                username='rtexerinha@gmail.com',
                email='rtexerinha@gmail.com',
                defaults={
                    'first_name': 'Rafael',
                    'last_name': 'Texerinha',
                    'is_staff': False,
                    'is_active': True,
                }
            )
            if created:
                regular_user.set_password('123456')
                regular_user.save()

            # Create customer profile for regular user
            customer, created = Customer.objects.get_or_create(
                user=regular_user,
                defaults={
                    'first_name': 'Rafael',
                    'last_name': 'Texerinha',
                    'email': 'rtexerinha@gmail.com',
                    'cellphone': '+1987654321',
                    'address': '456 Customer Ave',
                    'city': 'Los Angeles',
                    'zip': '90210'
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created regular user: {regular_user.username}')
                )
            else:
                self.stdout.write(f'Regular user already exists: {regular_user.username}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded users!')
        )
        self.stdout.write('Login credentials:')
        self.stdout.write('Organizer - Email: calisamba@gmail.com, Password: 123456')
        self.stdout.write('Customer - Email: rtexerinha@gmail.com, Password: 123456')
