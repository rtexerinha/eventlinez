from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from customer.models import Customer
from event.models import Promoter


class Command(BaseCommand):
    help = 'Check user details and optionally reset password'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to check')
        parser.add_argument(
            '--reset-password',
            action='store_true',
            help='Reset the user password to 123456',
        )

    def handle(self, *args, **options):
        email = options['email']

        try:
            user = User.objects.get(username=email)
            self.stdout.write(f"User found: {user.username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"First name: {user.first_name}")
            self.stdout.write(f"Last name: {user.last_name}")
            self.stdout.write(f"Is active: {user.is_active}")
            self.stdout.write(f"Is staff: {user.is_staff}")
            self.stdout.write(f"Is superuser: {user.is_superuser}")
            self.stdout.write(f"Last login: {user.last_login}")
            self.stdout.write(f"Date joined: {user.date_joined}")

            # Check if user has promoter profile
            try:
                promoter = Promoter.objects.get(user=user)
                self.stdout.write(f"Promoter profile: {promoter.name}")
            except Promoter.DoesNotExist:
                self.stdout.write("No promoter profile found")

            # Check if user has customer profile
            try:
                customer = Customer.objects.get(user=user)
                self.stdout.write(f"Customer profile: {customer.first_name} {customer.last_name}")
            except Customer.DoesNotExist:
                self.stdout.write("No customer profile found")

            # Test password
            is_password_correct = user.check_password('123456')
            self.stdout.write(f"Password '123456' is correct: {is_password_correct}")

            if options['reset_password']:
                user.set_password('123456')
                user.save()
                self.stdout.write(
                    self.style.SUCCESS('Password reset to 123456')
                )

        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} not found')
            )
