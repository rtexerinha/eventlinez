from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from event.models import Category
from address.models import State, City


class Command(BaseCommand):
    help = 'Check database connection and current data'

    def handle(self, *args, **options):
        self.stdout.write('🔍 DATABASE CONNECTION CHECK')
        self.stdout.write('=' * 60)

        # Show database configuration
        db_config = settings.DATABASES['default']
        self.stdout.write('📊 DATABASE CONFIG:')
        self.stdout.write(f"Engine: {db_config.get('ENGINE', 'Not set')}")
        self.stdout.write(f"Name: {db_config.get('NAME', 'Not set')}")
        self.stdout.write(f"Host: {db_config.get('HOST', 'localhost')}")
        self.stdout.write(f"Port: {db_config.get('PORT', 'default')}")
        self.stdout.write(f"User: {db_config.get('USER', 'Not set')}")

        # Test connection
        self.stdout.write('\n🔌 CONNECTION TEST:')
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version()")
                version = cursor.fetchone()[0]
                self.stdout.write(f"✅ Connected to: {version}")

                # Get current database name
                cursor.execute("SELECT current_database()")
                current_db = cursor.fetchone()[0]
                self.stdout.write(f"📁 Current database: {current_db}")

        except Exception as e:
            self.stdout.write(f"❌ Connection failed: {e}")
            return

        # Check table existence
        self.stdout.write('\n📋 TABLE CHECK:')
        tables_to_check = [
            'event_category',
            'address_state', 
            'address_city',
            'event_event',
            'auth_user'
        ]

        with connection.cursor() as cursor:
            for table in tables_to_check:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.stdout.write(f"✅ {table}: {count} records")
                except Exception as e:
                    self.stdout.write(f"❌ {table}: {e}")

        # Check Django models
        self.stdout.write('\n🎭 DJANGO MODELS CHECK:')
        try:
            categories = Category.objects.all()
            self.stdout.write(f"Categories: {categories.count()} records")
            if categories.exists():
                self.stdout.write("  Sample categories:")
                for cat in categories[:5]:
                    self.stdout.write(f"    - {cat.name}")
        except Exception as e:
            self.stdout.write(f"❌ Categories error: {e}")

        try:
            states = State.objects.all()
            cities = City.objects.all()
            self.stdout.write(f"States: {states.count()} records")
            self.stdout.write(f"Cities: {cities.count()} records")
            if states.exists():
                for state in states:
                    city_count = City.objects.filter(state=state).count()
                    self.stdout.write(f"  - {state.name}: {city_count} cities")
        except Exception as e:
            self.stdout.write(f"❌ Location models error: {e}")

        # Show environment info
        self.stdout.write('\n🌍 ENVIRONMENT:')
        import os
        self.stdout.write(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE', 'Not set')}")
        self.stdout.write(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'Not set')[:50]}...")

        self.stdout.write('\n🔧 RECOMMENDATIONS:')
        if Category.objects.count() == 0:
            self.stdout.write("  - Run: make seed-categories")
        if City.objects.count() == 0:
            self.stdout.write("  - Run: make seed-cities")
        if State.objects.count() == 0:
            self.stdout.write("  - Run: make seed-locations-categories")
