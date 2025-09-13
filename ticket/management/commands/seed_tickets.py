from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction, models
from django.utils import timezone
from event.models import Event, Ticket as EventTicket
from ticket.models import Ticket
from customer.models import Customer
from order.models import Order, OrderItem
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Seed tickets with test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing tickets before seeding',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of tickets to create per event (default: 3)',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing tickets...')
            Ticket.objects.all().delete()

        # Get customer user
        try:
            customer_user = User.objects.get(username='rtexerinha@gmail.com')
            customer = Customer.objects.get(user=customer_user)
        except (User.DoesNotExist, Customer.DoesNotExist):
            self.stdout.write(
                self.style.ERROR('Customer user not found. Please run seed_users first.')
            )
            return

        # Get events
        events = Event.objects.all()
        if not events.exists():
            self.stdout.write(
                self.style.ERROR('No events found. Please run seed_events first.')
            )
            return

        count = options['count']

        with transaction.atomic():
            for event in events:
                # First, create event tickets (ticket types) for this event if they don't exist
                event_ticket, created = EventTicket.objects.get_or_create(
                    name=f'General Admission - {event.name}',
                    event=event,
                    defaults={
                        'quantity': 100,
                        'price': Decimal('50.00'),
                        'sold_out': False,
                    }
                )

                if created:
                    self.stdout.write(f'Created event ticket type: {event_ticket.name}')

                # Create a dummy order for the tickets
                order, created = Order.objects.get_or_create(
                    customer=customer,
                    defaults={
                        'total': Decimal('0.00'),
                        'token': f'ORDER-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                        'emailAddress': customer.email,
                        'payment_code': 'SEED_DATA',
                        'billingName': f'{customer.first_name} {customer.last_name}',
                        'billingAddress1': customer.address or 'Test Address',
                        'billingCity': customer.city or 'Test City',
                        'billingPostcode': customer.zip or '00000',
                        'billingCountry': 'US',
                    }
                )

                if created:
                    self.stdout.write(f'Created order: {order.id}')

                # Create order item (this will automatically create tickets via post_save signal)
                order_item, created = OrderItem.objects.get_or_create(
                    order=order,
                    event_ticket=event_ticket,
                    defaults={
                        'quantity': count,
                        'unit_price': event_ticket.price,
                        'fee': Decimal('2.50'),  # Small processing fee
                        'amount': event_ticket.price * count + Decimal('2.50'),
                    }
                )

                if created:
                    self.stdout.write(f'Created order item: {order_item.id} (tickets created automatically)')

                    # Update order total
                    order.total = order.orderitem_set.aggregate(
                        total=models.Sum('amount')
                    )['total'] or Decimal('0.00')
                    order.save()

                    # Randomly set some tickets as checked in after they're created
                    created_tickets = Ticket.objects.filter(order_item=order_item)
                    for ticket in created_tickets:
                        if random.choice([True, False, False]):  # 1/3 chance of being checked in
                            ticket.checkin_date = timezone.now() - timezone.timedelta(days=random.randint(1, 10))
                            ticket.save()
                            self.stdout.write(f'Checked in ticket: {ticket.id}')

        total_tickets = Ticket.objects.count()
        checked_in_tickets = Ticket.objects.filter(checkin_date__isnull=False).count()
        pending_tickets = Ticket.objects.filter(checkin_date__isnull=True).count()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded tickets!')
        )
        self.stdout.write(f'Total tickets created: {total_tickets}')
        self.stdout.write(f'Checked in tickets: {checked_in_tickets}')
        self.stdout.write(f'Pending tickets: {pending_tickets}')
