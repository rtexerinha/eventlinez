from django.test import TestCase

from .models import CartItem

from model_bakery import baker


class TestCartItem(TestCase):

    def test_round_fee(self):
        cart = baker.make('cart.Cart')
        event = baker.make('event.Event', description="foo")
        ticket = baker.make('event.Ticket', event=event, quantity=10, price=50)

        with self.settings(EVENTLINEZ_FEE=0.09):
            item = CartItem.objects.create(ticket=ticket, quantity=2, cart=cart)
            self.assertEqual(9, item.fee())

    def test_amount(self):
        cart = baker.make('cart.Cart')
        event1 = baker.make('event.Event', description="foo")
        ticket1 = baker.make('event.Ticket', event=event1, price=50)

        event2 = baker.make('event.Event', description="foo")
        ticket2 = baker.make('event.Ticket', event=event2, price=150)

        with self.settings(EVENTLINEZ_FEE=0.09):
            CartItem.objects.create(ticket=ticket1, quantity=2, cart=cart)
            CartItem.objects.create(ticket=ticket2, quantity=1, cart=cart)

            self.assertEqual(272.5, cart.amount())
