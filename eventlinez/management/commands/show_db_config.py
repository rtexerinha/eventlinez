from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Show current database configuration'

    def handle(self, *args, **options):
        self.stdout.write('🔧 DJANGO DATABASE CONFIGURATION')
        self.stdout.write('=' * 50)

        db_config = settings.DATABASES['default']

        self.stdout.write('Current settings:')
        self.stdout.write(f"  Engine: {db_config.get('ENGINE')}")
        self.stdout.write(f"  Name: {db_config.get('NAME')}")
        self.stdout.write(f"  Host: {db_config.get('HOST', 'localhost')}")
        self.stdout.write(f"  Port: {db_config.get('PORT', 5432)}")
        self.stdout.write(f"  User: {db_config.get('USER')}")
        self.stdout.write(f"  Password: {'*' * len(str(db_config.get('PASSWORD', '')))} ({len(str(db_config.get('PASSWORD', '')))} chars)")

        self.stdout.write('\nEnvironment variables:')
        self.stdout.write(f"  DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')}")
        self.stdout.write(f"  DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}")

        # Expected Docker PostgreSQL config
        self.stdout.write('\n📋 EXPECTED DOCKER CONFIG:')
        self.stdout.write('  Host: localhost (or eventlinez_db if inside container)')
        self.stdout.write('  Port: 5432')
        self.stdout.write('  Database: eventlinez')
        self.stdout.write('  User: eventlinez')
        self.stdout.write('  Password: Texera123@')

        # Check if we're using the right database
        expected_db = db_config.get('NAME') == 'eventlinez'
        expected_user = db_config.get('USER') == 'eventlinez'
        expected_engine = 'postgresql' in db_config.get('ENGINE', '')

        self.stdout.write('\n✅ CONFIGURATION CHECK:')
        self.stdout.write(f"  PostgreSQL engine: {'✅' if expected_engine else '❌'}")
        self.stdout.write(f"  Database name: {'✅' if expected_db else '❌'}")
        self.stdout.write(f"  User name: {'✅' if expected_user else '❌'}")

        if not all([expected_engine, expected_db, expected_user]):
            self.stdout.write(f'\n🔧 TO FIX: Update your .env file with:')
            self.stdout.write(f'  DATABASE_URL=postgresql://eventlinez:Texera123@@localhost:5432/eventlinez')
