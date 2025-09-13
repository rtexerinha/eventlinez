from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from customer.models import Customer
from event.models import Category, Promoter, Event, Ticket
from address.models import State, City


class Command(BaseCommand):
    help = 'Check what data exists in the database'

    def handle(self, *args, **options):
        self.stdout.write('=== DATABASE CONTENTS ===\n')

        # Users
        users = User.objects.all()
        self.stdout.write(f'👥 USERS ({users.count()}):')
        for user in users:
            self.stdout.write(f'  - {user.username} ({user.email}) - {user.first_name} {user.last_name}')

        # Customers
        customers = Customer.objects.all()
        self.stdout.write(f'\n👤 CUSTOMERS ({customers.count()}):')
        for customer in customers:
            self.stdout.write(f'  - {customer.first_name} {customer.last_name} ({customer.email})')

        # States
        states = State.objects.all()
        self.stdout.write(f'\n🗺️  STATES ({states.count()}):')
        for state in states:
            self.stdout.write(f'  - {state.name}')

        # Cities
        cities = City.objects.all()
        self.stdout.write(f'\n🏙️  CITIES ({cities.count()}):')
        for city in cities:
            self.stdout.write(f'  - {city.name}, {city.state.name}')

        # Categories
        categories = Category.objects.all()
        self.stdout.write(f'\n📂 CATEGORIES ({categories.count()}):')
        for category in categories:
            self.stdout.write(f'  - {category.name} ({category.slug})')

        # Promoters
        promoters = Promoter.objects.all()
        self.stdout.write(f'\n🎭 PROMOTERS ({promoters.count()}):')
        for promoter in promoters:
            self.stdout.write(f'  - {promoter.name} ({promoter.email})')

        # Events
        events = Event.objects.all()
        self.stdout.write(f'\n🎉 EVENTS ({events.count()}):')
        for event in events:
            self.stdout.write(f'  - {event.name} ({event.event_date})')

        # Tickets
        tickets = Ticket.objects.all()
        self.stdout.write(f'\n🎫 TICKETS ({tickets.count()}):')
        for ticket in tickets:
            self.stdout.write(f'  - {ticket.event.name}: {ticket.name} (${ticket.price})')

        self.stdout.write('\n=== END ===')
