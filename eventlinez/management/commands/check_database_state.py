from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import connection
from event.models import Event, Category, Promoter, Ticket as EventTicket
from customer.models import Customer
from ticket.models import Ticket
from order.models import Order, OrderItem


class Command(BaseCommand):
    help = 'Check the current state of all database tables'

    def handle(self, *args, **options):
        self.stdout.write('🔍 DATABASE STATE CHECK')
        self.stdout.write('=' * 60)

        # Check each model
        models_to_check = [
            ('Users', User),
            ('Promoters', Promoter),
            ('Customers', Customer),
            ('Categories', Category),
            ('Events', Event),
            ('Event Tickets', EventTicket),
            ('Orders', Order),
            ('Order Items', OrderItem),
            ('Tickets', Ticket),
        ]

        for name, model in models_to_check:
            count = model.objects.count()
            self.stdout.write(f'{name:15} : {count:3d} records')

            # Show some details for key models
            if name == 'Users' and count > 0:
                users = User.objects.all()[:5]
                for user in users:
                    self.stdout.write(f'    - {user.username} (Active: {user.is_active})')

            elif name == 'Events' and count > 0:
                events = Event.objects.all()[:5]
                for event in events:
                    self.stdout.write(f'    - {event.name} (Available: {event.available})')
                    self.stdout.write(f'      Promoter: {event.promoter.name}')

            elif name == 'Categories' and count > 0:
                categories = Category.objects.all()
                for cat in categories:
                    self.stdout.write(f'    - {cat.name} (slug: {cat.slug})')

        self.stdout.write('\n' + '=' * 60)

        # Check database tables directly
        self.stdout.write('📊 DIRECT TABLE CHECK (via SQL)')
        with connection.cursor() as cursor:
            # Check if tables exist and have data
            tables = [
                'auth_user',
                'event_promoter', 
                'customer_customer',
                'event_category',
                'event_event',
                'event_ticket',
                'order_order',
                'ticket_ticket'
            ]

            for table in tables:
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    self.stdout.write(f'{table:20} : {count:3d} records')
                except Exception as e:
                    self.stdout.write(f'{table:20} : ERROR - {e}')

        self.stdout.write('\n🔧 RECOMMENDATIONS:')

        # Check specific issues
        if User.objects.filter(username='calisamba@gmail.com').exists():
            self.stdout.write('✅ calisamba@gmail.com user exists')
        else:
            self.stdout.write('❌ calisamba@gmail.com user missing - run: make seed-users')

        if Promoter.objects.filter(user__username='calisamba@gmail.com').exists():
            self.stdout.write('✅ Promoter profile exists')
        else:
            self.stdout.write('❌ Promoter profile missing - run: make seed-users')

        if Category.objects.exists():
            self.stdout.write('✅ Categories exist')
        else:
            self.stdout.write('❌ Categories missing - run: make seed-events')

        if Event.objects.exists():
            self.stdout.write('✅ Events exist')
        else:
            self.stdout.write('❌ Events missing - run: make seed-events')
