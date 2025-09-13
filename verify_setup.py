#!/usr/bin/env python
"""
Comprehensive setup verification for EventLinez
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventlinez.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection
from event.models import Promoter, Event, Category
from customer.models import Customer
from ticket.models import Ticket
from order.models import Order


def check_database_connection():
    """Test database connection"""
    print("🔍 Checking database connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            result = cursor.fetchone()
            print(f"✅ Database connected: {result[0]}")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_users():
    """Check if seeded users exist and can authenticate"""
    print("\n👥 Checking users...")

    # Check organizer user
    try:
        user = User.objects.get(username='calisambaa@gmail.com')
        print(f"✅ Organizer user found: {user.username}")
        print(f"   - Active: {user.is_active}")
        print(f"   - Staff: {user.is_staff}")

        # Test password
        if user.check_password('123456'):
            print("   - Password: ✅ Correct")
        else:
            print("   - Password: ❌ Incorrect")

        # Check promoter profile
        try:
            promoter = Promoter.objects.get(user=user)
            print(f"   - Promoter profile: ✅ {promoter.name}")
        except Promoter.DoesNotExist:
            print("   - Promoter profile: ❌ Missing")

    except User.DoesNotExist:
        print("❌ Organizer user not found")

    # Check customer user
    try:
        user = User.objects.get(username='rtexerinha@gmail.com')
        print(f"✅ Customer user found: {user.username}")
        print(f"   - Active: {user.is_active}")

        # Test password
        if user.check_password('123456'):
            print("   - Password: ✅ Correct")
        else:
            print("   - Password: ❌ Incorrect")

        # Check customer profile
        try:
            customer = Customer.objects.get(user=user)
            print(f"   - Customer profile: ✅ {customer.first_name} {customer.last_name}")
        except Customer.DoesNotExist:
            print("   - Customer profile: ❌ Missing")

    except User.DoesNotExist:
        print("❌ Customer user not found")


def check_events():
    """Check if events were created"""
    print("\n🎉 Checking events...")
    events = Event.objects.all()
    print(f"Events found: {events.count()}")

    for event in events[:3]:  # Show first 3
        print(f"   - {event.name} (ID: {event.id})")


def check_tickets():
    """Check if tickets were created"""
    print("\n🎫 Checking tickets...")
    tickets = Ticket.objects.all()
    print(f"Tickets found: {tickets.count()}")

    if tickets.exists():
        checked_in = tickets.filter(checkin_date__isnull=False).count()
        pending = tickets.filter(checkin_date__isnull=True).count()
        print(f"   - Checked in: {checked_in}")
        print(f"   - Pending: {pending}")


def check_orders():
    """Check if orders were created"""
    print("\n📋 Checking orders...")
    orders = Order.objects.all()
    print(f"Orders found: {orders.count()}")


def fix_user_password(email, password='123456'):
    """Fix user password"""
    try:
        user = User.objects.get(username=email)
        user.set_password(password)
        user.save()
        print(f"✅ Password reset for {email}")
        return True
    except User.DoesNotExist:
        print(f"❌ User {email} not found")
        return False


def main():
    print("🚀 EventLinez Setup Verification")
    print("=" * 50)

    # Check database
    if not check_database_connection():
        print("\n❌ Database connection failed. Check your Docker containers:")
        print("Run: docker-compose ps")
        return

    # Check all components
    check_users()
    check_events()
    check_tickets()
    check_orders()

    print("\n🔧 Quick Fixes:")
    print("If login still doesn't work, try:")
    print("1. Reset passwords: python verify_setup.py --fix-passwords")
    print("2. Reseed data: make seed-fresh")
    print("3. Check pgAdmin at http://localhost:5050")
    print("   Login: admin@eventlinez.com / admin123")

    # Fix passwords if requested
    if '--fix-passwords' in sys.argv:
        print("\n🔧 Fixing passwords...")
        fix_user_password('calisambaa@gmail.com')
        fix_user_password('rtexerinha@gmail.com')


if __name__ == '__main__':
    main()
