#!/usr/bin/env python
"""
Simple script to test if the cart template is working correctly
"""

import requests
from bs4 import BeautifulSoup

def test_cart_template():
    """Test the cart template rendering"""
    try:
        # Test the main page first
        response = requests.get('http://localhost:8000/')
        if response.status_code == 200:
            print("✅ Main page is accessible")
        else:
            print(f"❌ Main page returned status {response.status_code}")
            return
        
        # Test cart page (should redirect to login)
        response = requests.get('http://localhost:8000/cart/')
        if response.status_code in [200, 302]:
            print("✅ Cart page is accessible (returns status {})".format(response.status_code))
            
            # If status is 200, check for template errors
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for the problematic template syntax
                content = response.text
                if '{{' in content and '}}' in content:
                    # Look for unrendered template variables
                    if '{{ total|floatformat:2' in content:
                        print("❌ Found unrendered template syntax in cart page")
                    else:
                        print("✅ No unrendered template syntax found")
                else:
                    print("✅ Template rendering appears to be working")
        else:
            print(f"❌ Cart page returned unexpected status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to http://localhost:8000/")
        print("   Make sure the Django server is running with Docker:")
        print("   docker compose up -d")
    except Exception as e:
        print(f"❌ Error testing cart template: {e}")

if __name__ == "__main__":
    test_cart_template()
