from django.core.management.base import BaseCommand
from django.db import transaction
from address.models import State, City


class Command(BaseCommand):
    help = 'Seed California cities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing cities and states before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing cities and states...')
            City.objects.all().delete()
            State.objects.all().delete()

        with transaction.atomic():
            # Create California state
            california, created = State.objects.get_or_create(
                name='California'
            )
            if created:
                self.stdout.write('✅ Created state: California')
            else:
                self.stdout.write('➡️ State already exists: California')

            # Major California cities
            california_cities = [
                'Los Angeles',
                'San Francisco',
                'San Diego',
                'San Jose',
                'Fresno',
                'Sacramento',
                'Long Beach',
                'Oakland',
                'Bakersfield',
                'Anaheim',
                'Santa Ana',
                'Riverside',
                'Stockton',
                'Irvine',
                'Chula Vista',
                'Fremont',
                'San Bernardino',
                'Modesto',
                'Fontana',
                'Oxnard',
                'Moreno Valley',
                'Huntington Beach',
                'Glendale',
                'Santa Clarita',
                'Garden Grove',
                'Santa Rosa',
                'Oceanside',
                'Rancho Cucamonga',
                'Ontario',
                'Lancaster',
                'Elk Grove',
                'Palmdale',
                'Corona',
                'Salinas',
                'Pomona',
                'Hayward',
                'Escondido',
                'Torrance',
                'Sunnyvale',
                'Orange',
                'Fullerton',
                'Pasadena',
                'Thousand Oaks',
                'Visalia',
                'Simi Valley',
                'Concord',
                'Roseville',
                'Rockville',
                'Santa Clara',
                'Vallejo',
                'Victorville',
                'El Monte',
                'Berkeley',
                'Downey',
                'Costa Mesa',
                'Inglewood',
                'Carlsbad',
                'San Buenaventura (Ventura)',
                'Fairfield',
                'West Covina',
                'Murrieta',
                'Richmond',
                'Norwalk',
                'Antioch',
                'Temecula',
                'Daly City',
                'Burbank',
                'Rialto',
                'Santa Maria',
                'El Cajon',
                'San Mateo',
                'Clovis',
                'Compton',
                'Jurupa Valley',
                'Vista',
                'South Gate',
                'Mission Viejo',
                'Vacaville',
                'Carson',
                'Hesperia',
                'Santa Monica',
                'Westminster',
                'Redding',
                'Santa Barbara',
                'Chico',
                'Newport Beach',
                'San Leandro',
                'San Marcos',
                'Whittier',
                'Hawthorne',
                'Citrus Heights',
                'Tracy',
                'Alhambra',
                'Livermore',
                'Buena Park',
                'Lakewood',
                'Merced',
                'Hemet',
                'Chino',
                'Menifee',
                'Lake Forest',
                'Napa',
                'Redwood City',
                'Bellflower',
                'Indio',
                'Tustin',
                'Baldwin Park',
                'Chino Hills',
                'Mountain View',
            ]

            created_count = 0
            existing_count = 0

            for city_name in california_cities:
                city, created = City.objects.get_or_create(
                    name=city_name,
                    defaults={'state': california}
                )

                if created:
                    created_count += 1
                    if created_count <= 10:  # Show first 10 for brevity
                        self.stdout.write(f'✅ Created city: {city_name}')
                else:
                    existing_count += 1

            # Show summary
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write('CALIFORNIA CITIES SUMMARY:')
            self.stdout.write(f'✅ Created: {created_count} cities')
            self.stdout.write(f'➡️ Already existed: {existing_count} cities')
            self.stdout.write(f'📊 Total California cities: {City.objects.filter(state=california).count()}')

            if created_count > 10:
                self.stdout.write(f'... and {created_count - 10} more cities created')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded California cities!')
        )
