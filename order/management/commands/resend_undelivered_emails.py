import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from order.models import OrderEmailLog

logger = logging.getLogger(__name__)

RESEND_AFTER_HOURS = 2


class Command(BaseCommand):
    help = 'Resend confirmation emails for orders with no delivery confirmation after 2 hours.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='List candidates without actually resending.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        cutoff = timezone.now() - timezone.timedelta(hours=RESEND_AFTER_HOURS)

        candidates = OrderEmailLog.objects.filter(
            sent_at__lte=cutoff,
            delivered_at__isnull=True,
            bounced=False,
            resent_at__isnull=True,
        ).select_related('order')

        if not candidates.exists():
            self.stdout.write('No undelivered emails found.')
            return

        self.stdout.write(f'Found {candidates.count()} undelivered email(s).')

        for log in candidates:
            order = log.order
            self.stdout.write(
                f'  Order #{order.id} → {log.email_to} '
                f'(sent {log.sent_at:%Y-%m-%d %H:%M} UTC)'
            )
            if dry_run:
                continue
            try:
                order.send_notification(is_resend=True)
                self.stdout.write(self.style.SUCCESS(f'    Resent OK'))
                logger.info(f'resend_undelivered_emails: resent order #{order.id} to {log.email_to}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'    Failed: {e}'))
                logger.error(f'resend_undelivered_emails: order #{order.id} failed — {e}')

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('Done.'))
        else:
            self.stdout.write('Dry run complete — nothing was sent.')
