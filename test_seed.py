#!/usr/bin/env python
"""
Simple script to test if we can import all the models correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventlinez.settings')
django.setup()

try:
    from address.models import State, City, Address
    print("✓ Address models imported successfully")
except ImportError as e:
    print(f"✗ Address models error: {e}")

try:
    from customer.models import Customer
    print("✓ Customer models imported successfully")
except ImportError as e:
    print(f"✗ Customer models error: {e}")

try:
    from event.models import Category, Promoter, Event, Ticket
    print("✓ Event models imported successfully")
except ImportError as e:
    print(f"✗ Event models error: {e}")

try:
    from promoter.models import BankAccount, Vendor, Payment
    print("✓ Promoter models imported successfully")
except ImportError as e:
    print(f"✗ Promoter models error: {e}")

try:
    from order.models import Order, OrderItem
    print("✓ Order models imported successfully")
except ImportError as e:
    print(f"✗ Order models error: {e}")

try:
    from cart.models import Cart, CartItem
    print("✓ Cart models imported successfully")
except ImportError as e:
    print(f"✗ Cart models error: {e}")

try:
    import ticket.models as ticket_models
    print("✓ Ticket models imported successfully")
except ImportError as e:
    print(f"✗ Ticket models error: {e}")

print("\nAll imports completed!")
