import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventlinez.settings')
django.setup()

import json
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction

from cart.models import Cart, CartItem
from event.models import Event, Ticket, Category, Promoter
from address.models import State, City
from customer.models import Customer
from promoter.models import Vendor


def debug_cart_functionality():
    """Debug cart functionality step by step"""
    print("🔍 DEBUGGING CART FUNCTIONALITY")
    print("=" * 50)
    
    client = Client()
    
    try:
        # Step 1: Check if we have any events and tickets
        print("\n1. Checking existing data...")
        events = Event.objects.all()
        tickets = Ticket.objects.all()
        carts = Cart.objects.all()
        cart_items = CartItem.objects.all()
        
        print(f"Events in database: {events.count()}")
        print(f"Tickets in database: {tickets.count()}")
        print(f"Carts in database: {carts.count()}")
        print(f"Cart items in database: {cart_items.count()}")
        
        if events.exists():
            for event in events[:3]:  # Show first 3 events
                event_tickets = Ticket.objects.filter(event=event)
                print(f"  Event: {event.name} - {event_tickets.count()} tickets")
                for ticket in event_tickets:
                    print(f"    - {ticket.name}: ${ticket.price} (qty: {ticket.quantity}, available: {ticket.qty_available()})")
        
        # Step 2: Test URL resolution
        print("\n2. Testing URL resolution...")
        try:
            cart_add_url = reverse('cart:add_cart')
            cart_detail_url = reverse('cart:detail')
            print(f"✅ Cart add URL: {cart_add_url}")
            print(f"✅ Cart detail URL: {cart_detail_url}")
        except Exception as e:
            print(f"❌ URL resolution error: {e}")
            return
        
        # Step 3: Test session creation
        print("\n3. Testing session creation...")
        session = client.session
        print(f"Initial session key: {session.session_key}")
        
        # Make a simple request to create session
        response = client.get('/')
        print(f"After GET request session key: {client.session.session_key}")
        
        # Step 4: Test cart add with real ticket data
        print("\n4. Testing cart add with real data...")
        
        if not tickets.exists():
            print("❌ No tickets found in database. Cannot test cart functionality.")
            return
        
        # Use the first available ticket
        test_ticket = tickets.first()
        print(f"Using test ticket: {test_ticket.name} (ID: {test_ticket.id})")
        
        # Test data
        test_data = {
            'tickets': [
                {'id': test_ticket.id, 'quantity': 1}
            ],
            'promo_code': None,
            'vendor_code': None
        }
        
        print(f"Sending data: {test_data}")
        
        # Make the request
        response = client.post(
            cart_add_url,
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.items())}")
        
        try:
            response_data = json.loads(response.content.decode())
            print(f"Response JSON: {response_data}")
        except:
            print(f"Response content (raw): {response.content}")
        
        # Step 5: Check if cart was created
        print("\n5. Checking cart creation...")
        carts_after = Cart.objects.all()
        cart_items_after = CartItem.objects.all()
        
        print(f"Carts after request: {carts_after.count()}")
        print(f"Cart items after request: {cart_items_after.count()}")
        
        for cart in carts_after:
            items = CartItem.objects.filter(cart=cart)
            print(f"  Cart {cart.cart_id}: {items.count()} items")
            for item in items:
                print(f"    - {item.ticket.name}: qty {item.quantity}")
        
        # Step 6: Test cart detail view
        print("\n6. Testing cart detail view...")
        response = client.get(cart_detail_url)
        print(f"Cart detail response status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if cart template is rendered correctly
            content = response.content.decode()
            if 'Your shopping cart is empty' in content:
                print("⚠️  Cart appears empty in template")
            elif 'cart_items' in str(response.context):
                cart_items_context = response.context.get('cart_items', [])
                print(f"Cart items in context: {len(list(cart_items_context))}")
            else:
                print("❌ Unexpected cart template content")
        
        # Step 7: Test with authentication
        print("\n7. Testing with authenticated user...")
        
        # Create a test user if needed
        test_user, created = User.objects.get_or_create(
            username='test@example.com',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print("✅ Created test user")
        
        # Login
        login_success = client.login(username='test@example.com', password='testpass123')
        print(f"Login success: {login_success}")
        
        if login_success:
            # Try adding to cart as authenticated user
            response = client.post(
                cart_add_url,
                data=json.dumps(test_data),
                content_type='application/json'
            )
            print(f"Authenticated cart add response: {response.status_code}")
            try:
                response_data = json.loads(response.content.decode())
                print(f"Authenticated response JSON: {response_data}")
            except:
                print(f"Authenticated response content: {response.content}")
        
        # Step 8: Manual cart creation test
        print("\n8. Testing manual cart creation...")
        
        try:
            with transaction.atomic():
                # Create cart manually
                session_key = client.session.session_key or 'manual-test-cart'
                manual_cart = Cart.objects.create(cart_id=session_key)
                
                # Create cart item manually
                manual_item = CartItem.objects.create(
                    cart=manual_cart,
                    ticket=test_ticket,
                    quantity=1,
                    active=True
                )
                
                print(f"✅ Manual cart created: {manual_cart}")
                print(f"✅ Manual cart item created: {manual_item}")
                
                # Test cart methods
                print(f"Cart subtotal: ${manual_cart.subtotal()}")
                print(f"Cart total: ${manual_cart.amount()}")
                
        except Exception as e:
            print(f"❌ Manual cart creation error: {e}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"❌ Debug failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🔍 CART DEBUG COMPLETED")


if __name__ == '__main__':
    debug_cart_functionality()