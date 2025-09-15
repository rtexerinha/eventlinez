"""
Django management command to create the sales_by_vendor view safely
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Create sales_by_vendor view safely after migrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force create view, dropping existing one first',
        )

    def handle(self, *args, **options):
        # Check if we're using PostgreSQL (view is only useful for PostgreSQL)
        if 'postgresql' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(
                self.style.WARNING('Not using PostgreSQL, skipping view creation')
            )
            return

        with connection.cursor() as cursor:
            try:
                # Check if all required tables exist
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('ticket_ticket', 'event_ticket', 'event_event', 'promoter_vendor')
                """)
                existing_tables = {row[0] for row in cursor.fetchall()}
                required_tables = {'ticket_ticket', 'event_ticket', 'event_event', 'promoter_vendor'}
                
                if not required_tables.issubset(existing_tables):
                    missing = required_tables - existing_tables
                    self.stdout.write(
                        self.style.WARNING(f'Missing required tables: {missing}. Skipping view creation.')
                    )
                    return

                # Drop existing view if force is specified
                if options['force']:
                    self.stdout.write('Dropping existing view...')
                    cursor.execute('DROP VIEW IF EXISTS sales_by_vendor CASCADE;')
                    self.stdout.write(
                        self.style.SUCCESS('Existing view dropped')
                    )

                # Create the view
                self.stdout.write('Creating sales_by_vendor view...')
                cursor.execute("""
                    CREATE VIEW sales_by_vendor AS
                    SELECT ee.id,
                           ee.id AS event_id,
                           ee.name AS event_name,
                           ev.id AS vendor_id,
                           ev.first_name AS vendor_name,
                           count(*) AS qty,
                           sum(tt.price) AS amount
                    FROM ticket_ticket tt,
                         event_ticket et,
                         event_event ee,
                         promoter_vendor ev
                    WHERE tt.event_ticket_id = et.id
                    AND et.event_id = ee.id
                    AND tt.vendor_id = ev.id
                    GROUP BY ee.id, ee.name, ev.id, ev.first_name;
                """)
                
                self.stdout.write(
                    self.style.SUCCESS('sales_by_vendor view created successfully')
                )

            except Exception as e:
                if 'already exists' in str(e).lower():
                    self.stdout.write(
                        self.style.WARNING('View already exists. Use --force to recreate.')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Error creating view: {e}')
                    )
                    raise
