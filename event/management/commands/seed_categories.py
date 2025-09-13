from django.core.management.base import BaseCommand
from django.db import transaction
from django.template.defaultfilters import slugify
from event.models import Category


class Command(BaseCommand):
    help = 'Seed music event categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing categories...')
            Category.objects.all().delete()

        # Music categories
        music_categories = [
            'Samba',
            'Funk',
            'Electronic', 
            'Hip-Hop',
            'Sertanejo',
            'Axé',
            'Rock',
            'Pop',
            'Jazz',
            'Blues',
            'Reggae',
            'Country',
            'Classical',
            'R&B',
            'Indie',
            'Alternative',
            'Metal',
            'Punk',
            'Folk',
            'Latin',
            'World Music',
            'Gospel',
            'Disco',
            'House',
            'Techno',
            'Trap',
            'Reggaeton',
            'Bossa Nova',
            'MPB',
            'Forró',
        ]

        with transaction.atomic():
            created_count = 0
            existing_count = 0

            self.stdout.write('🎵 Creating music categories...')

            for category_name in music_categories:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    defaults={'slug': slugify(category_name)}
                )

                if created:
                    created_count += 1
                    self.stdout.write(f'✅ Created category: {category_name}')
                else:
                    existing_count += 1
                    self.stdout.write(f'➡️ Category exists: {category_name}')

            # Show summary
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write('MUSIC CATEGORIES SUMMARY:')
            self.stdout.write(f'✅ Created: {created_count} categories')
            self.stdout.write(f'➡️ Already existed: {existing_count} categories')
            self.stdout.write(f'📊 Total categories: {Category.objects.count()}')

        # Show all categories
        self.stdout.write('\n🎼 ALL CATEGORIES:')
        categories = Category.objects.all().order_by('name')
        for i, category in enumerate(categories, 1):
            self.stdout.write(f'{i:2d}. {category.name} (slug: {category.slug})')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded music categories!')
        )
