from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

from customer.models import Customer
from event.models import Promoter


class Command(BaseCommand):
    help = "Lowercase all user emails/usernames to prevent case-sensitivity login issues."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without writing to the database.',
        )

    def handle(self, *_args, **options):
        dry_run = options['dry_run']
        changed = 0

        users_to_fix = [
            u for u in User.objects.all()
            if u.username != u.username.lower().strip() or u.email != u.email.lower().strip()
        ]
        customers_to_fix = [
            c for c in Customer.objects.all()
            if c.email != c.email.lower().strip()
        ]
        promoters_to_fix = [
            p for p in Promoter.objects.all()
            if p.email != p.email.lower().strip()
        ]

        for user in users_to_fix:
            self.stdout.write(f"  User #{user.id}: '{user.username}' → '{user.username.lower().strip()}'")

        changed = len(users_to_fix)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\nDRY RUN — {changed} user(s) would be updated. Run without --dry-run to apply."
            ))
            return

        with transaction.atomic():
            for user in users_to_fix:
                user.username = user.username.lower().strip()
                user.email = user.email.lower().strip()
                user.save(update_fields=['username', 'email'])

            for customer in customers_to_fix:
                customer.email = customer.email.lower().strip()
                customer.save(update_fields=['email'])

            for promoter in promoters_to_fix:
                promoter.email = promoter.email.lower().strip()
                promoter.save(update_fields=['email'])

        self.stdout.write(self.style.SUCCESS(
            f"Done — {changed} user(s) updated to lowercase."
        ))
