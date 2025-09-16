"""
Django management command to drop problematic database views before migrations
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Drop problematic database views that block migrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force drop views without confirmation',
        )

    def handle(self, *args, **options):
        # Check if we're using PostgreSQL
        if 'postgresql' not in settings.DATABASES['default']['ENGINE']:
            self.stdout.write(
                self.style.WARNING('Not using PostgreSQL, skipping view cleanup')
            )
            return

        views_to_drop = [
            'sales_by_vendor',
            'public.sales_by_vendor',
            'ticket_report',
            'public.ticket_report',
        ]

        with connection.cursor() as cursor:
            # First, check if views exist
            cursor.execute("""
                SELECT viewname FROM pg_views 
                WHERE schemaname = 'public' 
                AND viewname IN ('sales_by_vendor', 'ticket_report')
            """)
            existing_views = [row[0] for row in cursor.fetchall()]
            
            if not existing_views:
                self.stdout.write(
                    self.style.SUCCESS('No problematic views found to drop')
                )
            
            for view_name in views_to_drop:
                try:
                    self.stdout.write(f'Attempting to drop view: {view_name}')
                    cursor.execute(f'DROP VIEW IF EXISTS {view_name} CASCADE;')
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully dropped view: {view_name}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Could not drop view {view_name}: {e}')
                    )

            # Show remaining views for verification
            try:
                cursor.execute(
                    "SELECT schemaname, viewname FROM pg_views WHERE schemaname = 'public';"
                )
                views = cursor.fetchall()
                if views:
                    self.stdout.write('\nRemaining views in public schema:')
                    for schema, view in views:
                        self.stdout.write(f'  - {schema}.{view}')
                else:
                    self.stdout.write('\nNo views found in public schema')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Could not list views: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS('View cleanup completed')
        )
