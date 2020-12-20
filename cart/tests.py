from django.test import TestCase

from .models import CartItem

from model_bakery import baker


class TestCartItem(TestCase):

    def test_round_fee(self):
        cart = baker.make('cart.Cart')
        event = baker.make('event.Event', description="foo", stock=10, unit_price=50)

        with self.settings(EVENTLINEZ_FEE=0.09):
            item = CartItem.objects.create(event=event, quantity=2, cart=cart)
            self.assertEqual(9, item.fee())
