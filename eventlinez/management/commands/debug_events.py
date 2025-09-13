from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from event.models import Event, Promoter
from customer.models import Customer


class Command(BaseCommand):
    help = 'Debug events and promoter relationships'

    def handle(self, *args, **options):
        self.stdout.write('🔍 DEBUGGING EVENTS AND PROMOTERS')
        self.stdout.write('=' * 50)

        # Check calisamba@gmail.com user
        try:
            user = User.objects.get(username='calisamba@gmail.com')
            self.stdout.write(f'✅ User found: {user.username}')
            self.stdout.write(f'   - ID: {user.id}')
            self.stdout.write(f'   - Active: {user.is_active}')
            self.stdout.write(f'   - Staff: {user.is_staff}')
        except User.DoesNotExist:
            self.stdout.write('❌ User calisamba@gmail.com not found')
            return

        # Check promoter profile
        try:
            promoter = Promoter.objects.get(user=user)
            self.stdout.write(f'✅ Promoter found: {promoter.name}')
            self.stdout.write(f'   - ID: {promoter.id}')
            self.stdout.write(f'   - Email: {promoter.email}')
        except Promoter.DoesNotExist:
            self.stdout.write('❌ Promoter profile not found')
            return

        # Check all events
        all_events = Event.objects.all()
        self.stdout.write(f'\n📅 TOTAL EVENTS IN DATABASE: {all_events.count()}')

        if all_events.exists():
            self.stdout.write('\nALL EVENTS:')
            for event in all_events:
                self.stdout.write(f'  - {event.name} (ID: {event.id})')
                self.stdout.write(f'    Promoter: {event.promoter.name} (ID: {event.promoter.id})')
                self.stdout.write(f'    Promoter User: {event.promoter.user.username}')
                self.stdout.write(f'    Available: {event.available}')
                self.stdout.write('')

        # Check events for this specific promoter
        promoter_events = Event.objects.filter(promoter=promoter)
        self.stdout.write(f'📋 EVENTS FOR {promoter.name}: {promoter_events.count()}')

        if promoter_events.exists():
            self.stdout.write('\nPROMOTER EVENTS:')
            for event in promoter_events:
                self.stdout.write(f'  ✅ {event.name}')
        else:
            self.stdout.write('❌ No events found for this promoter')

        # Check events by user
        user_events = Event.objects.filter(promoter__user=user)
        self.stdout.write(f'\n👤 EVENTS BY USER {user.username}: {user_events.count()}')

        # Check all promoters
        all_promoters = Promoter.objects.all()
        self.stdout.write(f'\n👥 ALL PROMOTERS: {all_promoters.count()}')
        for p in all_promoters:
            event_count = Event.objects.filter(promoter=p).count()
            self.stdout.write(f'  - {p.name} ({p.user.username}): {event_count} events')

        # Recommendations
        self.stdout.write('\n🔧 RECOMMENDATIONS:')
        if all_events.exists() and not promoter_events.exists():
            self.stdout.write('  - Run: make fix-event-ownership')
        elif not all_events.exists():
            self.stdout.write('  - Run: make seed-events or make seed')
        else:
            self.stdout.write('  - Events look correct, check the dashboard view logic')
