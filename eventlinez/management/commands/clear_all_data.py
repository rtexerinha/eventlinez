from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction


class Command(BaseCommand):
    help = 'Clear all seeded data from the database (keeps superusers)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING('This will delete ALL data except superusers!')
            )
            self.stdout.write('Run with --confirm to proceed')
            self.stdout.write('Example: python manage.py clear_all_data --confirm')
            return

        self.stdout.write('Clearing all data...')

        try:
            with transaction.atomic():
                # Import models
                from ticket.models import Ticket
                from order.models import OrderItem, Order
                from event.models import Event, Ticket as EventTicket, Category, Promoter
                from customer.models import Customer

                # Delete in the correct order to avoid foreign key constraints
                deleted_counts = {}

                # Tickets
                count = Ticket.objects.count()
                Ticket.objects.all().delete()
                deleted_counts['Tickets'] = count

                # Orders
                order_items_count = OrderItem.objects.count()
                orders_count = Order.objects.count()
                OrderItem.objects.all().delete()
                Order.objects.all().delete()
                deleted_counts['Order Items'] = order_items_count
                deleted_counts['Orders'] = orders_count

                # Event Tickets and Events
                event_tickets_count = EventTicket.objects.count()
                events_count = Event.objects.count()
                EventTicket.objects.all().delete()
                Event.objects.all().delete()
                deleted_counts['Event Tickets'] = event_tickets_count
                deleted_counts['Events'] = events_count

                # Categories
                categories_count = Category.objects.count()
                Category.objects.all().delete()
                deleted_counts['Categories'] = categories_count

                # Promoters and Customers
                promoters_count = Promoter.objects.count()
                customers_count = Customer.objects.count()
                Promoter.objects.all().delete()
                Customer.objects.all().delete()
                deleted_counts['Promoters'] = promoters_count
                deleted_counts['Customers'] = customers_count

                # Users (excluding superusers)
                users_count = User.objects.filter(is_superuser=False).count()
                User.objects.filter(is_superuser=False).delete()
                deleted_counts['Users'] = users_count

                # Show summary
                self.stdout.write('\n' + '=' * 50)
                self.stdout.write('DELETION SUMMARY:')
                for model, count in deleted_counts.items():
                    self.stdout.write(f'  {model}: {count} deleted')

                self.stdout.write('\n' + self.style.SUCCESS('All data cleared successfully!'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error clearing data: {e}')
            )
            raise
