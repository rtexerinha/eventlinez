#!/usr/bin/env python
"""
Standalone script to check Stripe charges for missing or incomplete descriptions.

This script can be run without Django if needed, by providing the Stripe API key
as an environment variable.

Usage:
    # Using environment variable
    export STRIPE_SECRET_KEY=sk_live_yourkey
    python check_stripe_descriptions.py
    
    # Or inline
    STRIPE_SECRET_KEY=sk_live_yourkey python check_stripe_descriptions.py
    
    # With Django (recommended - has more features)
    python manage.py audit_stripe_descriptions --limit 100 --fix
"""
import os
import sys
from datetime import datetime

try:
    import stripe
except ImportError:
    print("❌ Error: stripe package not installed. Run: pip install stripe")
    sys.exit(1)


def check_missing_descriptions(limit=100):
    """Check Stripe charges for missing descriptions."""
    
    # Get API key from environment
    api_key = os.getenv("STRIPE_SECRET_KEY")
    
    if not api_key:
        print("❌ Error: STRIPE_SECRET_KEY environment variable not set")
        print("\nUsage:")
        print("  export STRIPE_SECRET_KEY=sk_live_yourkey")
        print("  python check_stripe_descriptions.py")
        sys.exit(1)
    
    stripe.api_key = api_key
    
    print(f"\n🔍 Checking Stripe Charges (limit: {limit})")
    print("=" * 60)
    
    try:
        charges = stripe.Charge.list(limit=limit)
    except stripe.error.AuthenticationError:
        print("❌ Error: Invalid Stripe API key")
        sys.exit(1)
    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e}")
        sys.exit(1)
    
    missing = []
    
    for ch in charges.data:
        description = ch.description or ''
        metadata = ch.metadata or {}
        
        has_description = bool(description and description.strip())
        has_event_name = 'event_name' in metadata
        has_order_id = 'order_id' in metadata
        has_proper_format = 'Order #' in description or '/' in description
        
        if not (has_description and has_proper_format):
            missing.append({
                'charge_id': ch.id,
                'amount': ch.amount / 100.0,
                'created': datetime.fromtimestamp(ch.created),
                'description': description,
                'has_event_name': has_event_name,
                'has_order_id': has_order_id,
                'metadata': metadata,
                'payment_intent': ch.payment_intent,
            })
    
    # Display results
    print(f"\n📊 Results:")
    print(f"Total charges checked: {len(charges.data)}")
    print(f"Charges with missing/incomplete info: {len(missing)}\n")
    
    if missing:
        print(f"⚠️  Found {len(missing)} charges missing information:\n")
        
        for item in missing:
            print("-" * 60)
            print(f"Charge ID: {item['charge_id']}")
            print(f"Amount: ${item['amount']:.2f}")
            print(f"Created: {item['created'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Description: {item['description'] or '❌ Missing'}")
            print(f"Has event_name in metadata: {'✅' if item['has_event_name'] else '❌'}")
            print(f"Has order_id in metadata: {'✅' if item['has_order_id'] else '❌'}")
            
            if item['metadata']:
                print("Metadata:", dict(item['metadata']))
            
            if item['payment_intent']:
                print(f"PaymentIntent: {item['payment_intent']}")
            
            print()
    else:
        print("✅ All charges have proper descriptions!")
    
    # Show recommendations
    if missing:
        print("\n💡 Recommendations:")
        print("  1. Use the Django management command for automated fixes:")
        print("     python manage.py audit_stripe_descriptions --fix")
        print("  2. Ensure your checkout flow sets descriptions properly")
        print("  3. Review cart/views.py and order/views.py for proper Stripe integration")
        print("\n  Example of proper description:")
        print("     'Calisamba in San Diego 2025/Tier 1 (Order #5142)'")


def main():
    """Main entry point."""
    # Allow custom limit via command line argument
    limit = 100
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
        except ValueError:
            print(f"⚠️  Invalid limit: {sys.argv[1]}, using default: 100")
    
    check_missing_descriptions(limit)


if __name__ == "__main__":
    main()

