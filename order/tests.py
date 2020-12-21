from django.test import TestCase
from django.core import mail
from model_bakery import baker

from .models import OrderItem


class OrderMailTest(TestCase):

    def setUp(self):
        self.order = baker.make('order.Order', emailAddress="me@gmail.com")
        event = baker.make('event.Event', description="foo", stock=2, unit_price=100)

        with self.settings(EVENTLINEZ_FEE=0.10):
            order_item1 = OrderItem(event=event, quantity=1, price=100, amount=100, fee=10, order=self.order)
            order_item2 = OrderItem(event=event, quantity=1, price=100,  amount=100, fee=10, order=self.order)

            order_item1.save()
            order_item2.save()

    def test_send_mail(self):
        self.order.send_notification()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].to, [self.order.emailAddress])
        self.assertEqual(mail.outbox[0].subject, "Eventlinez - New Order #" + str(self.order.id))


class OrderTicketGeneration(TestCase):

    def test_create_order_item_should_create_a_ticket(self):
        event = baker.make('event.Event', description="foo",  unit_price=50)
        event.save()
        order = baker.make('order.Order')
        order.save()

        with self.settings(EVENTLINEZ_FEE=0.10):
            order_item1 = OrderItem(quantity=2, price=50, amount=100, fee=10,  order=order, event=event)
            order_item1.save()

        from event.models import Ticket
        self.assertEqual(Ticket.objects.count(), 2)

    def test_create_order_should_decrease_ticket_quantity(self):
        event = baker.make('event.Event', description="foo", stock=1, unit_price=50)
        event.save()
        order = baker.make('order.Order')
        order.save()

        with self.settings(EVENTLINEZ_FEE=0.10):
            order_item1 = OrderItem(quantity=1, price=100,  amount=100, fee=10, order=order, event=event)
            order_item1.save()

        event.refresh_from_db()
        self.assertEqual(event.stock, 0)
