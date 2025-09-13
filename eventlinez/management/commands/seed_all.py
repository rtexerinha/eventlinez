from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Seed all data (users, events, tickets) in the correct order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)

        self.stdout.write('Starting data seeding process...')
        self.stdout.write('=' * 50)

        # Seed locations and categories first
        self.stdout.write('1. Seeding locations and categories...')
        call_command('seed_locations_categories', clear=clear)
        self.stdout.write('')

        # Seed users second
        self.stdout.write('2. Seeding users...')
        call_command('seed_users', clear=clear)
        self.stdout.write('')

        # Seed events third
        self.stdout.write('3. Seeding events...')
        call_command('seed_events', clear=clear)
        self.stdout.write('')

        # Seed tickets last
        self.stdout.write('3. Seeding tickets...')
        call_command('seed_tickets', clear=clear)
        self.stdout.write('')

        # Fix event ownership to ensure all events belong to calisambaa@gmail.com
        self.stdout.write('4. Fixing event ownership...')
        call_command('fix_event_ownership')
        self.stdout.write('')

        self.stdout.write('=' * 50)
        self.stdout.write(
            self.style.SUCCESS('All data seeded successfully!')
        )
        self.stdout.write('')
        self.stdout.write('Test credentials:')
        self.stdout.write('Organizer: calisamba@gmail.com / 123456')
        self.stdout.write('Customer: rtexerinha@gmail.com / 123456')
