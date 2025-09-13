from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Seed both California cities and music categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)

        self.stdout.write('🌟 SEEDING LOCATIONS AND CATEGORIES')
        self.stdout.write('=' * 60)

        # Seed cities first
        self.stdout.write('1. Seeding California cities...')
        call_command('seed_cities', clear=clear)
        self.stdout.write('')

        # Seed categories second
        self.stdout.write('2. Seeding music categories...')
        call_command('seed_categories', clear=clear)
        self.stdout.write('')

        self.stdout.write('=' * 60)
        self.stdout.write(
            self.style.SUCCESS('All locations and categories seeded successfully!')
        )

        # Show final summary
        from address.models import City, State
        from event.models import Category

        states_count = State.objects.count()
        cities_count = City.objects.count()
        categories_count = Category.objects.count()

        self.stdout.write('\n📊 FINAL SUMMARY:')
        self.stdout.write(f'States: {states_count}')
        self.stdout.write(f'Cities: {cities_count}')
        self.stdout.write(f'Categories: {categories_count}')
