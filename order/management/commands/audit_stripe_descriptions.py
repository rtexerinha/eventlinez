"""
Django management command to audit Stripe charges for missing or incomplete descriptions.

Usage:
    python manage.py audit_stripe_descriptions [--limit 100] [--fix]

Options:
    --limit N    Limit the number of charges to check (default: 100)
    --fix        Attempt to fix missing descriptions by looking up orders
"""
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import stripe


class Command(BaseCommand):
    help = 'Audit Stripe charges for missing or incomplete descriptions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Number of recent charges to audit (default: 100)'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix missing descriptions by updating PaymentIntents'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Check all charges (paginate through all)'
        )

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        if not stripe.api_key or stripe.api_key.startswith('sk_test_512345'):
            self.stdout.write(self.style.ERROR('Stripe API key not properly configured'))
            return
        
        limit = options['limit']
        fix_mode = options['fix']
        check_all = options['all']
        
        self.stdout.write(self.style.SUCCESS(f'\n🔍 Auditing Stripe Charges'))
        self.stdout.write(f'Limit: {limit if not check_all else "ALL"}')
        self.stdout.write(f'Fix mode: {"ON" if fix_mode else "OFF"}\n')
        
        missing_charges = []
        total_checked = 0
        fixed_count = 0
        
        try:
            # Retrieve charges from Stripe
            if check_all:
                charges = stripe.Charge.list(limit=100)
                for charge in charges.auto_paging_iter():
                    total_checked += 1
                    result = self._check_charge(charge)
                    if not result['has_description']:
                        missing_charges.append(result)
                        if fix_mode:
                            fixed = self._attempt_fix(charge, result)
                            if fixed:
                                fixed_count += 1
            else:
                charges = stripe.Charge.list(limit=limit)
                for charge in charges.data:
                    total_checked += 1
                    result = self._check_charge(charge)
                    if not result['has_description']:
                        missing_charges.append(result)
                        if fix_mode:
                            fixed = self._attempt_fix(charge, result)
                            if fixed:
                                fixed_count += 1
        
        except stripe.error.AuthenticationError:
            self.stdout.write(self.style.ERROR('Stripe authentication failed. Check your API key.'))
            return
        except stripe.error.StripeError as e:
            self.stdout.write(self.style.ERROR(f'Stripe error: {e}'))
            return
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f'\n📊 Audit Results'))
        self.stdout.write(f'Total charges checked: {total_checked}')
        self.stdout.write(f'Charges with missing/incomplete info: {len(missing_charges)}')
        
        if fix_mode:
            self.stdout.write(self.style.SUCCESS(f'Successfully fixed: {fixed_count}'))
        
        if missing_charges:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Found {len(missing_charges)} charges with missing information:\n'))
            
            for result in missing_charges:
                self.stdout.write('-' * 60)
                self.stdout.write(f'Charge ID: {result["charge_id"]}')
                self.stdout.write(f'Amount: ${result["amount"]:.2f}')
                self.stdout.write(f'Created: {result["created"]}')
                self.stdout.write(f'Description: {result["description"] or "❌ Missing"}')
                self.stdout.write(f'Has event_name: {result["has_event_name"]}')
                self.stdout.write(f'Has order_id: {result["has_order_id"]}')
                if result.get('payment_intent'):
                    self.stdout.write(f'PaymentIntent: {result["payment_intent"]}')
                self.stdout.write('')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ All charges have proper descriptions!'))
        
        # Summary recommendations
        if missing_charges and not fix_mode:
            self.stdout.write(self.style.WARNING('\n💡 Recommendations:'))
            self.stdout.write('  1. Run with --fix to attempt automatic fixes')
            self.stdout.write('  2. Check if your checkout flow is setting descriptions properly')
            self.stdout.write('  3. Review the updated cart/views.py and order/views.py code')

    def _check_charge(self, charge):
        """Check if a charge has proper description and metadata."""
        description = charge.description or ''
        metadata = charge.metadata or {}
        
        has_description = bool(description and description.strip())
        has_event_name = 'event_name' in metadata and bool(metadata.get('event_name'))
        has_order_id = 'order_id' in metadata and bool(metadata.get('order_id'))
        has_proper_format = 'Order #' in description or '/' in description
        
        return {
            'charge_id': charge.id,
            'amount': charge.amount / 100.0,
            'created': datetime.fromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M:%S'),
            'description': description,
            'has_description': has_description and has_proper_format,
            'has_event_name': has_event_name,
            'has_order_id': has_order_id,
            'metadata': metadata,
            'payment_intent': charge.payment_intent,
        }

    def _attempt_fix(self, charge, result):
        """Attempt to fix a charge by looking up the order and updating the PaymentIntent."""
        from order.models import Order
        from order.stripe_utils import build_stripe_description, build_stripe_metadata_from_order
        
        try:
            # Try to find order by payment_code (which stores the payment_intent ID)
            payment_intent_id = charge.payment_intent
            if not payment_intent_id:
                self.stdout.write(self.style.WARNING(f'  ⚠️  No PaymentIntent for charge {charge.id}'))
                return False
            
            # Look up order by payment_code
            try:
                order = Order.objects.get(payment_code=payment_intent_id)
            except Order.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  ⚠️  No order found for PaymentIntent {payment_intent_id}'))
                return False
            
            # Build proper description and metadata
            order_items = order.orderitem_set.all()
            first_item = order_items.first()
            
            if not first_item:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Order {order.id} has no items'))
                return False
            
            event_name = first_item.event_ticket.event.name
            tier_name = first_item.event_ticket.name
            description = build_stripe_description(event_name, tier_name, order_id=order.id)
            metadata = build_stripe_metadata_from_order(order)
            
            # Update the PaymentIntent
            stripe.PaymentIntent.modify(
                payment_intent_id,
                description=description,
                metadata=metadata
            )
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ Fixed charge {charge.id} (Order #{order.id})'))
            self.stdout.write(f'     Description: {description}')
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Failed to fix charge {charge.id}: {e}'))
            return False

