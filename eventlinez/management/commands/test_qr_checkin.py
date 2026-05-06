"""
Management command: test_qr_checkin

Verifies the QR code check-in pipeline end-to-end:
  1. Lists recent purchased tickets with their check-in URLs
  2. Validates QR code SVG is well-formed and scannable
  3. Tests the check-in view via Django's test client
  4. Tests the doorman scan API endpoint

Usage:
    python manage.py test_qr_checkin
    python manage.py test_qr_checkin --ticket-id 9397
    python manage.py test_qr_checkin --email promoter@example.com
"""

from django.core.management.base import BaseCommand
from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.urls import reverse


class Command(BaseCommand):
    help = 'Test QR code generation and check-in API end-to-end'

    def add_arguments(self, parser):
        parser.add_argument('--ticket-id', type=int, help='Test a specific ticket ID')
        parser.add_argument('--email', type=str, help='Promoter email to use for auth tests')
        parser.add_argument('--limit', type=int, default=5, help='Number of recent tickets to show')

    def handle(self, *args, **options):
        from ticket.models import Ticket
        from eventlinez import settings

        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('QR CODE CHECK-IN PIPELINE TEST'))
        self.stdout.write('='*60 + '\n')

        # ── 1. APP_HOST check ────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('1. APP_HOST configuration'))
        host = settings.APP_HOST
        self.stdout.write(f'   APP_HOST = {host}')
        if host.endswith('/'):
            self.stdout.write(self.style.WARNING('   ⚠ APP_HOST has trailing slash — will produce double-slash URLs'))
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ No trailing slash'))

        expected_url_prefix = host.rstrip('/') + '/promoter/ticket/checkin/'
        self.stdout.write(f'   QR code URL format: {expected_url_prefix}<uuid>/')

        # ── 2. List tickets ──────────────────────────────────────────
        self.stdout.write('\n' + self.style.MIGRATE_HEADING('2. Recent purchased tickets'))
        qs = Ticket.objects.select_related(
            'event_ticket__event', 'day_event', 'customer'
        ).order_by('-created_at')

        if options['ticket_id']:
            qs = qs.filter(id=options['ticket_id'])
        else:
            qs = qs[:options['limit']]

        tickets = list(qs)
        if not tickets:
            self.stdout.write(self.style.WARNING('   No tickets found in database.'))
            return

        for t in tickets:
            effective = t.day_event if t.day_event else t.event_ticket.event
            url = f"{host.rstrip('/')}/promoter/ticket/checkin/{t.uuid}/"
            day_info = f' (Day {t.day_number})' if t.day_number else ''
            checked = '✓ CHECKED IN' if t.checkin_date else '○ not checked in'
            self.stdout.write(
                f'   Ticket #{t.id}{day_info} | {effective.name} | {checked}'
            )
            self.stdout.write(f'     UUID  : {t.uuid}')
            self.stdout.write(f'     URL   : {url}')

        # ── 3. QR SVG validation ─────────────────────────────────────
        self.stdout.write('\n' + self.style.MIGRATE_HEADING('3. QR code SVG validation'))
        test_ticket = tickets[0]
        svg = test_ticket.as_qrcode()

        has_viewbox = 'viewBox' in svg
        has_fixed_w = 'width="' in svg and 'mm"' in svg
        has_path = '<path' in svg or '<rect' in svg
        has_svg_tag = '<svg' in svg

        self.stdout.write(f'   Ticket #{test_ticket.id} SVG:')
        self._check('SVG tag present', has_svg_tag)
        self._check('viewBox present (enables CSS scaling)', has_viewbox)
        self._check('No fixed mm dimensions (CSS can control size)', not has_fixed_w)
        self._check('QR modules present (path/rect elements)', has_path)
        self.stdout.write(f'   SVG size: {len(svg):,} bytes')

        # ── 4. URL routing check ─────────────────────────────────────
        self.stdout.write('\n' + self.style.MIGRATE_HEADING('4. URL routing check'))
        try:
            url = reverse('promoter:ticket_checkin', kwargs={'checkin': test_ticket.uuid})
            self._check(f'ticket_checkin URL resolves → {url}', True)
        except Exception as e:
            self._check(f'ticket_checkin URL resolves', False, str(e))

        # ── 5. Check-in view test (promoter auth) ────────────────────
        self.stdout.write('\n' + self.style.MIGRATE_HEADING('5. Check-in view (promoter auth)'))
        promoter_user = self._get_promoter_user(options.get('email'))
        if promoter_user:
            self._test_checkin_view(test_ticket, promoter_user)
        else:
            self.stdout.write(self.style.WARNING('   ⚠ No promoter user found — skipping view test'))
            self.stdout.write('     Pass --email <promoter_email> to test with a specific user')

        # ── 6. Doorman scan API test ─────────────────────────────────
        self.stdout.write('\n' + self.style.MIGRATE_HEADING('6. Doorman scan API (/api/doorman/scan/ticket/)'))
        from promoter.models import Partner
        doorman_partner = Partner.objects.filter(role='DOORMAN', disable=False).select_related('user', 'event').first()
        if doorman_partner:
            self._test_doorman_scan_api(doorman_partner)
        else:
            self.stdout.write(self.style.WARNING('   ⚠ No active doorman Partner found — skipping API test'))

        # ── 7. Summary ───────────────────────────────────────────────
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('TEST COMPLETE'))
        self.stdout.write('='*60 + '\n')

    # ── helpers ──────────────────────────────────────────────────────

    def _check(self, label, passed, detail=''):
        if passed:
            self.stdout.write(self.style.SUCCESS(f'   ✓ {label}'))
        else:
            msg = f'   ✗ {label}'
            if detail:
                msg += f' — {detail}'
            self.stdout.write(self.style.ERROR(msg))

    def _get_promoter_user(self, email=None):
        from ticket.models import Ticket
        from promoter.models import Promoter
        if email:
            p = Promoter.objects.select_related('user').filter(user__email=email).first()
            return p.user if p else None
        # Find a promoter who actually owns unchecked tickets
        t = Ticket.objects.filter(checkin_date__isnull=True).select_related(
            'event_ticket__event__promoter__user'
        ).first()
        return t.event_ticket.event.promoter.user if t else None

    def _test_checkin_view(self, ticket, user):
        from ticket.models import Ticket
        from django.utils import timezone
        from datetime import timedelta
        client = Client()
        client.force_login(user)

        # Only test tickets whose event is still within the 6-hour check-in window
        cutoff = timezone.now() - timedelta(hours=6)
        unchecked = Ticket.objects.filter(
            event_ticket__event__promoter=user.promoter,
            checkin_date__isnull=True,
            event_ticket__event__event_date__gte=cutoff,
        ).select_related('event_ticket__event').first()

        if not unchecked:
            self.stdout.write(self.style.WARNING(
                '   ⚠ No unchecked ticket within check-in window for this promoter — skipping'
            ))
            self.stdout.write('     (all tickets are for past events; test on production with real event data)')
            return

        url = reverse('promoter:ticket_checkin', kwargs={'checkin': unchecked.uuid})
        self.stdout.write(f'   Testing GET {url}  (ticket #{unchecked.id})')
        response = client.get(url, SERVER_NAME='localhost')
        self._check(f'HTTP {response.status_code} (expect 200)', response.status_code == 200,
                    response.content[:200].decode(errors='replace'))
        if response.status_code == 200:
            unchecked.refresh_from_db()
            self._check('Ticket marked checked-in in DB', unchecked.checkin_date is not None)
            unchecked.checkin_date = None
            unchecked.save(update_fields=['checkin_date'])
            self.stdout.write('   (check-in reversed — test data unchanged)')

    def _test_doorman_scan_api(self, partner):
        from rest_framework.test import APIClient
        from ticket.models import Ticket
        from django.db.models import Q

        event = partner.event
        self.stdout.write(f'   Doorman: {partner.user.email} → Event: {event.name}')

        ticket = Ticket.objects.filter(
            Q(event_ticket__event=event, day_event__isnull=True) | Q(day_event=event),
            checkin_date__isnull=True,
        ).first()

        if not ticket:
            self.stdout.write(self.style.WARNING("   ⚠ No unchecked tickets for this doorman's event"))
            return

        # DRF uses TokenAuthentication — must use APIClient.force_authenticate
        client = APIClient()
        client.force_authenticate(user=partner.user)

        url = reverse('promoter:api_doorman_scan_ticket')
        self.stdout.write(f'   POST {url}  uuid={ticket.uuid}  event_id={event.id}')
        response = client.post(url, {'uuid': str(ticket.uuid), 'event_id': event.id}, format='json', SERVER_NAME='localhost')

        self._check(f'HTTP {response.status_code} (expect 200)', response.status_code == 200,
                    response.content[:300].decode(errors='replace'))
        try:
            data = response.json()
        except Exception:
            self._check('Response is valid JSON', False, response.content[:200].decode(errors='replace'))
            return

        self._check('success=True in response', data.get('success') is True, str(data))
        self.stdout.write(f'   message   : {data.get("message")}')
        self.stdout.write(f'   guest_name: {data.get("guest_name")}')
        self.stdout.write(f'   event_name: {data.get("event_name")}')

        if data.get('success'):
            ticket.refresh_from_db()
            self._check('Ticket marked checked-in in DB', ticket.checkin_date is not None)
            ticket.checkin_date = None
            ticket.save(update_fields=['checkin_date'])
            self.stdout.write('   (check-in reversed — test data unchanged)')
