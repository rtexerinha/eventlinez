from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.template.defaultfilters import slugify
from event.models import Category
from address.models import State, City


class Command(BaseCommand):
    help = 'Seed categories and cities directly to current database with verification'

    def handle(self, *args, **options):
        self.stdout.write('🎯 SEEDING DIRECTLY TO DATABASE')
        self.stdout.write('=' * 50)

        # First verify database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(), current_user, version()")
                db_info = cursor.fetchone()
                self.stdout.write(f'📊 Connected to: {db_info[0]}')
                self.stdout.write(f'👤 User: {db_info[1]}')
                self.stdout.write(f'🗄️ Version: {db_info[2][:50]}...')
        except Exception as e:
            self.stdout.write(f'❌ Database connection error: {e}')
            return

        with transaction.atomic():
            # 1. SEED MUSIC CATEGORIES
            self.stdout.write('\n🎵 SEEDING CATEGORIES...')
            music_categories = [
                'Samba', 'Funk', 'Electronic', 'Hip-Hop', 'Sertanejo', 'Axé',
                'Rock', 'Pop', 'Jazz', 'Blues', 'Reggae', 'Country', 'Classical',
                'R&B', 'Indie', 'Alternative', 'Metal', 'Latin', 'Gospel'
            ]

            category_count = 0
            for cat_name in music_categories:
                category, created = Category.objects.get_or_create(
                    name=cat_name,
                    defaults={'slug': slugify(cat_name)}
                )
                if created:
                    category_count += 1
                    self.stdout.write(f'✅ {cat_name}')

            self.stdout.write(f'📊 Created {category_count} categories')

            # 2. SEED CALIFORNIA STATE AND CITIES
            self.stdout.write('\n🏙️ SEEDING CALIFORNIA CITIES...')

            # Create California state
            california, created = State.objects.get_or_create(name='California')
            if created:
                self.stdout.write('✅ Created California state')

            # Key California cities
            ca_cities = [
                'Los Angeles', 'San Francisco', 'San Diego', 'San Jose', 'Sacramento',
                'Oakland', 'Santa Ana', 'Anaheim', 'Riverside', 'Stockton',
                'Bakersfield', 'Fremont', 'Irvine', 'Chula Vista', 'San Bernardino',
                'Modesto', 'Fontana', 'Santa Clarita', 'Moreno Valley', 'Glendale',
                'Huntington Beach', 'Santa Rosa', 'Oxnard', 'Rancho Cucamonga',
                'Ontario', 'Lancaster', 'Elk Grove', 'Corona', 'Palmdale',
                'Salinas', 'Pomona', 'Hayward', 'Torrance', 'Escondido',
                'Sunnyvale', 'Orange', 'Fullerton', 'Pasadena', 'Thousand Oaks',
                'Visalia', 'Simi Valley', 'Concord', 'Santa Clara', 'Vallejo'
            ]

            city_count = 0
            for city_name in ca_cities:
                city, created = City.objects.get_or_create(
                    name=city_name,
                    defaults={'state': california}
                )
                if created:
                    city_count += 1
                    if city_count <= 10:  # Show first 10
                        self.stdout.write(f'✅ {city_name}')

            self.stdout.write(f'📊 Created {city_count} cities')

            # 3. VERIFY RESULTS
            self.stdout.write('\n🔍 VERIFICATION:')

            # Check categories
            total_categories = Category.objects.count()
            self.stdout.write(f'Categories in DB: {total_categories}')
            if total_categories > 0:
                sample_cats = Category.objects.all()[:5]
                for cat in sample_cats:
                    self.stdout.write(f'  - {cat.name} (slug: {cat.slug})')

            # Check cities
            total_cities = City.objects.count()
            ca_cities_count = City.objects.filter(state__name='California').count()
            self.stdout.write(f'Total cities in DB: {total_cities}')
            self.stdout.write(f'California cities: {ca_cities_count}')

            # Direct SQL verification
            self.stdout.write('\n🔍 DIRECT SQL CHECK:')
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM event_category")
                sql_categories = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM address_city")
                sql_cities = cursor.fetchone()[0]

                self.stdout.write(f'Categories (SQL): {sql_categories}')
                self.stdout.write(f'Cities (SQL): {sql_cities}')

        self.stdout.write(f'\n✅ COMPLETED! Refresh your event form now.')
