from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Fix and test database connection to PostgreSQL'

    def handle(self, *args, **options):
        self.stdout.write('🔧 FIXING DATABASE CONNECTION')
        self.stdout.write('=' * 50)

        # Show current configuration
        db_config = settings.DATABASES['default']
        self.stdout.write('Current Django database config:')
        self.stdout.write(f"  Engine: {db_config.get('ENGINE')}")
        self.stdout.write(f"  Name: {db_config.get('NAME')}")
        self.stdout.write(f"  Host: {db_config.get('HOST', 'Not set')}")
        self.stdout.write(f"  Port: {db_config.get('PORT', 'Not set')}")
        self.stdout.write(f"  User: {db_config.get('USER', 'Not set')}")

        # Check if PostgreSQL
        if 'postgresql' in db_config.get('ENGINE', ''):
            self.stdout.write('✅ PostgreSQL engine configured')
        else:
            self.stdout.write('❌ Still using SQLite - check your .env file')
            self.stdout.write('Add this to your .env file:')
            self.stdout.write('DATABASE_URL=postgresql://eventlinez:Texera123@localhost:5432/eventlinez')
            return

        # Test connection
        self.stdout.write('\n🔌 Testing PostgreSQL connection...')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version(), current_database(), current_user")
                result = cursor.fetchone()
                self.stdout.write('✅ PostgreSQL connection successful!')
                self.stdout.write(f'  Version: {result[0][:50]}...')
                self.stdout.write(f'  Database: {result[1]}')
                self.stdout.write(f'  User: {result[2]}')

                # Test table existence
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name IN 
                    ('event_category', 'address_city', 'event_event')
                    LIMIT 5
                """)
                tables = cursor.fetchall()
                self.stdout.write(f'\n📊 Found {len(tables)} Django tables in PostgreSQL')
                for table in tables:
                    self.stdout.write(f'  ✅ {table[0]}')

        except Exception as e:
            self.stdout.write(f'❌ PostgreSQL connection failed: {e}')
            self.stdout.write('\n🔧 Troubleshooting:')
            self.stdout.write('1. Make sure Docker containers are running: make docker-status')
            self.stdout.write('2. Check if PostgreSQL is accessible: telnet localhost 5432')
            self.stdout.write('3. Verify .env file has: DATABASE_URL=postgresql://eventlinez:Texera123@localhost:5432/eventlinez')
            return

        self.stdout.write('\n✅ Database connection is working properly!')
        self.stdout.write('You can now run: make seed-all')
