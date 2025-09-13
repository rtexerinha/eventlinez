from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from event.models import Event, Promoter


class Command(BaseCommand):
    help = 'Fix event ownership to ensure all events belong to calisambaa@gmail.com'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        try:
            # Get the organizer user and promoter
            organizer_user = User.objects.get(username='calisamba@gmail.com')
            promoter = Promoter.objects.get(user=organizer_user)

            self.stdout.write(f"Found organizer: {organizer_user.username}")
            self.stdout.write(f"Found promoter: {promoter.name}")

        except (User.DoesNotExist, Promoter.DoesNotExist) as e:
            self.stdout.write(
                self.style.ERROR(f'Organizer user or promoter not found: {e}')
            )
            return

        # Get all events
        events = Event.objects.all()

        if not events.exists():
            self.stdout.write('No events found in database')
            return

        self.stdout.write(f"Found {events.count()} events")
        self.stdout.write("-" * 50)

        updated_count = 0

        with transaction.atomic():
            for event in events:
                needs_update = False
                changes = []

                # Check if promoter needs to be updated
                if event.promoter != promoter:
                    needs_update = True
                    changes.append(f"promoter: {event.promoter} -> {promoter}")

                # Check if we have a created_by field and it needs updating
                if hasattr(event, 'created_by') and event.created_by != organizer_user:
                    needs_update = True
                    changes.append(f"created_by: {event.created_by} -> {organizer_user}")

                if needs_update:
                    self.stdout.write(f"Event: {event.name}")
                    for change in changes:
                        self.stdout.write(f"  - {change}")

                    if not dry_run:
                        event.promoter = promoter
                        if hasattr(event, 'created_by'):
                            event.created_by = organizer_user
                        event.save()
                        updated_count += 1
                        self.stdout.write("  ✅ Updated")
                    else:
                        self.stdout.write("  🔍 Would be updated (dry run)")
                else:
                    self.stdout.write(f"Event: {event.name} - Already correct")

        if dry_run:
            self.stdout.write(f"\nDry run completed. {len([e for e in events if e.promoter != promoter])} events would be updated.")
        else:
            self.stdout.write(f"\n✅ Updated {updated_count} events")

        # Show final summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("FINAL SUMMARY:")
        for event in Event.objects.all():
            self.stdout.write(f"{event.name}:")
            self.stdout.write(f"  - Promoter: {event.promoter.name}")
            self.stdout.write(f"  - Promoter User: {event.promoter.user.username}")
