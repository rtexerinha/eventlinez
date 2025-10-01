from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Test email sending functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing email configuration...')
        
        # Check email settings
        self.stdout.write(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'EMAIL_HOST: {settings.EMAIL_HOST}')
        self.stdout.write(f'EMAIL_PORT: {settings.EMAIL_PORT}')
        self.stdout.write(f'EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}')
        self.stdout.write(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}')
        
        try:
            # Send test email
            send_mail(
                subject='Test Email from Eventlinez',
                message='This is a test email to verify SendGrid configuration is working.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],  # Change this to your email
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS('✅ Test email sent successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send email: {e}')
            )
