#!/usr/bin/env python
"""
Debug script to investigate cart detail view 400 error - exact test replication
"""
import os
import sys
import django
import tempfile
from django.conf import settings

# Add the project directory to the path
sys.path.append('/Users/rafaelteixeira/PycharmProjects/eventlinez')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventlinez.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from model_bakery import baker
from event.models import Event, Ticket


class CartDetailDebug:
    def __init__(self):
        self.client = Client()
    
    def debug_exact_test_conditions(self):
        """Debug using exact same conditions as the failing test"""
        print("🔍 DEBUGGING EXACT TEST CONDITIONS")
        print("=" * 60)
        
        # Replicate exact test setup
        image = tempfile.NamedTemporaryFile(suffix=".jpg").name
        print(f"Created temp image path: {image}")
        print(f"Image file exists: {os.path.exists(image)}")
        
        event = baker.make(Event, description="foo", image=image)
        pista = baker.make(Ticket, event=event, quantity=40, price=10)
        frontstage = baker.make(Ticket, event=event, quantity=20, price=20)
        camarote = baker.make(Ticket, event=event, quantity=10, price=40)
        
        print(f"Created event: {event.name}")
        print(f"Event image: {event.image}")
        print(f"Created tickets: pista, frontstage, camarote")
        
        # Exact same payload as test
        payload = {
            "promocode": None,
            "tickets": [
                {"id": camarote.id, "quantity": 1},
                {"id": frontstage.id, "quantity": 1},
                {"id": pista.id, "quantity": 0},
            ]
        }
        
        print(f"Adding items with payload: {payload}")
        add_response = self.client.post(reverse('cart:add_cart'), payload, 'application/json')
        print(f"Add response: {add_response.status_code} - {add_response.content}")
        
        # Test cart detail access (exact same as failing test)
        print(f"Session key: {self.client.session.session_key}")
        
        try:
            response = self.client.get(reverse("cart:detail"))
            print(f"Cart detail response status: {response.status_code}")
            
            if response.status_code == 400:
                print("❌ 400 ERROR REPRODUCED!")
                print(f"Response content (first 1000 chars): {response.content[:1000]}")
                
                # Try to capture any exception details
                try:
                    content_str = response.content.decode('utf-8')
                    if 'error' in content_str.lower():
                        print(f"Error in response: {content_str[:500]}")
                except:
                    pass
                    
            elif response.status_code == 200:
                print("✅ 200 SUCCESS - Test should pass")
                print(f"Response contains 'Cart summary': {'Cart summary' in response.content.decode('utf-8')}")
            else:
                print(f"Unexpected status code: {response.status_code}")
                
        except Exception as e:
            print(f"Exception during cart detail access: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 60)


if __name__ == '__main__':
    debugger = CartDetailDebug()
    debugger.debug_exact_test_conditions()