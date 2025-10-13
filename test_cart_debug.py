import json
import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.test.utils import override_settings
from unittest.mock import patch

from cart.models import Cart, CartItem
from event.models import Event, Ticket, Category, Promoter
from address.models import State, City
from customer.models import Customer
from promoter.models import Vendor


class CartDebugTestCase(TestCase):
    """Comprehensive test suite to debug cart functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123'
        )
        
        # Create customer
        self.customer = Customer.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            email='testuser@example.com'
        )
        
        # Create promoter user and promoter
        self.promoter_user = User.objects.create_user(
            username='promoter@example.com',
            email='promoter@example.com', 
            password='promoterpass123'
        )
        
        self.promoter = Promoter.objects.create(
            user=self.promoter_user,
            name='Test Promoter',
            email='promoter@example.com',
            address='123 Test St',
            city='Test City',
            zip='12345'
        )
        
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create state and city
        self.state = State.objects.create(name='Test State')
        self.city = City.objects.create(name='Test City', state=self.state)
        
        # Create event
        from django.utils import timezone
        from datetime import timedelta
        
        self.event = Event.objects.create(
            name='Test Event',
            slug='test-event',
            category=self.category,
            description='Test event description',
            event_date=timezone.now() + timedelta(days=30),
            address='123 Event St',
            city=self.city,
            promoter=self.promoter,
            available=True
        )
        
        # Create tickets
        self.ticket1 = Ticket.objects.create(
            name='General Admission',
            event=self.event,
            price=50.00,
            quantity=100,
            sold_out=False
        )
        
        self.ticket2 = Ticket.objects.create(
            name='VIP',
            event=self.event,
            price=100.00,
            quantity=50,
            sold_out=False
        )
        
        # Create vendor
        self.vendor = Vendor.objects.create(
            first_name='Test',
            last_name='Vendor',
            email='vendor@example.com',
            promoter=self.promoter
        )
        
        self.client = Client()
    
    def test_session_creation(self):
        """Test that sessions are created properly"""
        print("\n=== Testing Session Creation ===")
        
        # Test session creation
        session = self.client.session
        print(f"Initial session key: {session.session_key}")
        
        # Force session creation
        session.create()
        print(f"After create(): {session.session_key}")
        
        # Test with a request
        response = self.client.get('/')
        print(f"After GET request: {self.client.session.session_key}")
        
        self.assertIsNotNone(self.client.session.session_key)
    
    def test_cart_creation_manual(self):
        """Test manual cart creation"""
        print("\n=== Testing Manual Cart Creation ===")
        
        # Create session first
        session = self.client.session
        session.create()
        cart_id = session.session_key
        print(f"Using cart_id: {cart_id}")
        
        # Create cart manually
        cart = Cart.objects.create(cart_id=cart_id)
        print(f"Created cart: {cart}")
        print(f"Cart ID: {cart.cart_id}")
        print(f"Cart date_added: {cart.date_added}")
        
        # Verify cart exists
        retrieved_cart = Cart.objects.get(cart_id=cart_id)
        self.assertEqual(cart, retrieved_cart)
    
    def test_cart_add_endpoint_structure(self):
        """Test the cart add endpoint structure and routing"""
        print("\n=== Testing Cart Add Endpoint ===")
        
        # Test URL resolution
        try:
            url = reverse('cart:add_cart')
            print(f"Cart add URL: {url}")
        except Exception as e:
            print(f"URL resolution error: {e}")
            self.fail(f"Failed to resolve cart:add_cart URL: {e}")
        
        # Test basic POST to endpoint (without data)
        response = self.client.post(url)
        print(f"Empty POST response status: {response.status_code}")
        print(f"Empty POST response content: {response.content}")
    
    def test_cart_add_with_invalid_data(self):
        """Test cart add with various invalid data scenarios"""
        print("\n=== Testing Cart Add with Invalid Data ===")
        
        url = reverse('cart:add_cart')
        
        # Test 1: No data
        response = self.client.post(url, content_type='application/json')
        print(f"No data - Status: {response.status_code}, Content: {response.content}")
        
        # Test 2: Invalid JSON
        response = self.client.post(url, data='invalid json', content_type='application/json')
        print(f"Invalid JSON - Status: {response.status_code}, Content: {response.content}")
        
        # Test 3: Empty tickets array
        data = {'tickets': []}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        print(f"Empty tickets - Status: {response.status_code}, Content: {response.content}")
        
        # Test 4: Missing ticket ID
        data = {'tickets': [{'quantity': 1}]}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        print(f"Missing ticket ID - Status: {response.status_code}, Content: {response.content}")
        
        # Test 5: Non-existent ticket ID
        data = {'tickets': [{'id': 99999, 'quantity': 1}]}
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')
        print(f"Non-existent ticket - Status: {response.status_code}, Content: {response.content}")
    
    def test_cart_add_with_valid_data(self):
        """Test cart add with valid data"""
        print("\n=== Testing Cart Add with Valid Data ===")
        
        url = reverse('cart:add_cart')
        
        # Prepare valid data
        data = {
            'tickets': [
                {'id': self.ticket1.id, 'quantity': 2},
                {'id': self.ticket2.id, 'quantity': 1}
            ],
            'promo_code': None,
            'vendor_code': None
        }
        
        print(f"Sending data: {data}")
        
        # Send request
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        
        # Check if cart was created
        carts = Cart.objects.all()
        print(f"Carts in database: {carts.count()}")
        for cart in carts:
            print(f"  Cart: {cart.cart_id} - {cart.date_added}")
            items = CartItem.objects.filter(cart=cart)
            print(f"    Items: {items.count()}")
            for item in items:
                print(f"      {item.ticket.name}: {item.quantity}")
    
    def test_ticket_availability(self):
        """Test ticket availability calculation"""
        print("\n=== Testing Ticket Availability ===")
        
        print(f"Ticket 1 ({self.ticket1.name}):")
        print(f"  Price: ${self.ticket1.price}")
        print(f"  Quantity: {self.ticket1.quantity}")
        print(f"  Sold out: {self.ticket1.sold_out}")
        print(f"  Available: {self.ticket1.qty_available()}")
        
        print(f"Ticket 2 ({self.ticket2.name}):")
        print(f"  Price: ${self.ticket2.price}")
        print(f"  Quantity: {self.ticket2.quantity}")
        print(f"  Sold out: {self.ticket2.sold_out}")
        print(f"  Available: {self.ticket2.qty_available()}")
    
    def test_cart_detail_view(self):
        """Test cart detail view"""
        print("\n=== Testing Cart Detail View ===")
        
        # First add some items to cart
        self.test_cart_add_with_valid_data()
        
        # Now test cart detail
        self.client.login(username='testuser@example.com', password='testpass123')
        
        url = reverse('cart:detail')
        response = self.client.get(url)
        
        print(f"Cart detail status: {response.status_code}")
        print(f"Cart detail context keys: {list(response.context.keys()) if response.context else 'No context'}")
        
        if response.context:
            print(f"Cart items: {response.context.get('cart_items')}")
            print(f"Total: {response.context.get('total')}")
            print(f"Cart: {response.context.get('cart')}")
    
    def test_database_constraints(self):
        """Test database constraints and relationships"""
        print("\n=== Testing Database Constraints ===")
        
        # Test creating cart item without cart
        try:
            cart_item = CartItem.objects.create(
                ticket=self.ticket1,
                quantity=1
            )
            print("ERROR: Created cart item without cart!")
        except Exception as e:
            print(f"Good: Cannot create cart item without cart: {e}")
        
        # Test creating cart item with cart
        cart = Cart.objects.create(cart_id='test-cart-123')
        try:
            cart_item = CartItem.objects.create(
                ticket=self.ticket1,
                cart=cart,
                quantity=1
            )
            print(f"Success: Created cart item: {cart_item}")
        except Exception as e:
            print(f"Error creating cart item with cart: {e}")
    
    def run_all_debug_tests(self):
        """Run all debug tests in sequence"""
        print("🔍 STARTING COMPREHENSIVE CART DEBUG TESTS")
        print("=" * 60)
        
        try:
            self.test_session_creation()
            self.test_cart_creation_manual()
            self.test_cart_add_endpoint_structure()
            self.test_ticket_availability()
            self.test_database_constraints()
            self.test_cart_add_with_invalid_data()
            self.test_cart_add_with_valid_data()
            self.test_cart_detail_view()
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)
        print("🔍 CART DEBUG TESTS COMPLETED")


# Standalone test runner function
def run_cart_debug_tests():
    """Function to run cart debug tests"""
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    # Setup Django
    django.setup()
    
    # Create test instance
    test_case = CartDebugTestCase()
    test_case.setUp()
    test_case.run_all_debug_tests()


if __name__ == '__main__':
    run_cart_debug_tests()