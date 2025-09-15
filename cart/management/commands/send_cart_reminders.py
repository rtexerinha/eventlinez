from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from cart.utils import get_eligible_carts_for_reminder, cleanup_expired_carts
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send reminder emails to customers with abandoned carts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending emails',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Clean up expired carts first
        expired_count = cleanup_expired_carts()
        if expired_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Marked {expired_count} expired carts')
            )
        
        # Get eligible carts for reminders
        eligible_carts = get_eligible_carts_for_reminder()
        
        if not eligible_carts.exists():
            self.stdout.write(
                self.style.WARNING('No abandoned carts found that are eligible for reminders')
            )
            return
        
        self.stdout.write(
            f'Found {eligible_carts.count()} abandoned carts eligible for reminders'
        )
        
        sent_count = 0
        failed_count = 0
        
        for abandoned_cart in eligible_carts:
            try:
                if dry_run:
                    self.stdout.write(
                        f'[DRY RUN] Would send reminder to {abandoned_cart.email} '
                        f'for cart #{abandoned_cart.cart.id} (${abandoned_cart.total_amount})'
                    )
                    sent_count += 1
                else:
                    # Send actual reminder email
                    success = self.send_reminder_email(abandoned_cart)
                    if success:
                        abandoned_cart.mark_reminder_sent()
                        sent_count += 1
                        self.stdout.write(
                            f'Sent reminder to {abandoned_cart.email} '
                            f'for cart #{abandoned_cart.cart.id}'
                        )
                    else:
                        failed_count += 1
                        
            except Exception as e:
                failed_count += 1
                logger.error(f'Failed to send reminder for cart {abandoned_cart.cart.id}: {e}')
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to send reminder for cart #{abandoned_cart.cart.id}: {e}'
                    )
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'[DRY RUN] Would send {sent_count} reminder emails'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully sent {sent_count} reminder emails'
                )
            )
            if failed_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send {failed_count} emails')
                )

    def send_reminder_email(self, abandoned_cart):
        """
        Send reminder email for abandoned cart
        """
        try:
            subject = f'Complete your ticket purchase - {abandoned_cart.total_amount} waiting for you!'
            
            # Create email context
            context = {
                'customer_name': abandoned_cart.customer_name or 'Valued Customer',
                'total_amount': abandoned_cart.total_amount,
                'items_count': abandoned_cart.items_count,
                'cart_items': abandoned_cart.items.all(),
                'cart_url': f"{getattr(settings, 'APP_HOST', 'http://localhost:8000')}/cart/",
                'minutes_since_abandonment': abandoned_cart.minutes_since_abandonment,
            }
            
            # Render email templates
            html_message = render_to_string('cart/emails/cart_reminder.html', context)
            text_message = render_to_string('cart/emails/cart_reminder.txt', context)
            
            # Send email
            send_mail(
                subject=subject,
                message=text_message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@eventlinez.com'),
                recipient_list=[abandoned_cart.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return True
            
        except Exception as e:
            logger.error(f'Failed to send email to {abandoned_cart.email}: {e}')
            return False
