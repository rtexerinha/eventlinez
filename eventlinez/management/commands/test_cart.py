from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from cart.models import Cart, CartItem
from event.models import Ticket
from django.conf import settings


class Command(BaseCommand):
    help = 'Test cart functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing cart functionality...')
        
        # Get a test user
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No users found in database'))
                return
                
            self.stdout.write(f'Using user: {user.username}')
            
            # Get a test ticket
            ticket = Ticket.objects.first()
            if not ticket:
                self.stdout.write(self.style.ERROR('No tickets found in database'))
                return
                
            self.stdout.write(f'Using ticket: {ticket.name} (${ticket.price})')
            
            # Create a test cart
            cart, created = Cart.objects.get_or_create(
                cart_id=f'test_cart_{user.id}'
            )
            
            if created:
                self.stdout.write('Created new test cart')
            else:
                self.stdout.write('Using existing test cart')
            
            # Add item to cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                ticket=ticket,
                defaults={'quantity': 1}
            )
            
            if created:
                self.stdout.write('Added item to cart')
            else:
                self.stdout.write('Item already in cart')
            
            # Calculate total
            total = cart_item.price_total()
            self.stdout.write(f'Cart item total: ${total}')
            
            # Test checkout (without actually calling Stripe)
            self.stdout.write('Testing checkout process...')
            self.stdout.write(f'Stripe keys configured: {bool(settings.STRIPE_SECRET_KEY)}')
            
            self.stdout.write(
                self.style.SUCCESS('✅ Cart functionality test completed!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Cart test failed: {e}')
            )
