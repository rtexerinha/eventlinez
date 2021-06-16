from django.test import TestCase
from django.core import mail
from model_bakery import baker

from .models import Order
from ticket.models import Ticket
from .models import OrderItem


class OrderModel(TestCase):

    def setUp(self):
        event = baker.make('event.Event', description="foo")
        self.event_ticket1 = baker.make('event.Ticket', event=event, quantity=10, price=100)
        self.event_ticket2 = baker.make('event.Ticket', event=event, quantity=5, price=200)

    def test_ticket_qty(self):
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        baker.make(OrderItem, event_ticket=self.event_ticket1, quantity=1, order=order)
        baker.make(OrderItem, event_ticket=self.event_ticket1, quantity=3, order=order)
        self.assertEqual(order.ticket_qty(), 4)

    def test_ticket_qty_com_ordem_sem_linha(self):
        event = baker.make('event.Event', description="foo", stock=10, unit_price=100)
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        self.assertEqual(order.ticket_qty(), 0)

    def test_guest_name_deve_ser_o_customer_quando_uma_ordem_tiver_apenas_um_ticket(self):
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        item1 = baker.make(OrderItem, event_ticket=self.event_ticket1, quantity=1, order=order)

        tiket1 = Ticket.objects.get(order_item=item1)
        self.assertEqual(tiket1.guest_name, order.customer.first_name + " " + order.customer.last_name)

        event2 = baker.make('event.Event', description="foo2")
        event3 = baker.make('event.Event', description="foo3")
        order2 = baker.make('order.Order', emailAddress="me@gmail.com")
        item1 = baker.make(OrderItem, event_ticket=self.event_ticket1, quantity=1, order=order2)
        item2 = baker.make(OrderItem, event_ticket=self.event_ticket2, quantity=1, order=order2)

        tiket1 = Ticket.objects.get(order_item=item1)
        tiket2 = Ticket.objects.get(order_item=item2)
        self.assertEqual(tiket1.guest_name, order2.customer.first_name + " " + order2.customer.last_name)
        self.assertEqual(tiket2.guest_name, order2.customer.first_name + " " + order2.customer.last_name)


class OrderMailTest(TestCase):

    def test_send_mail(self):
        event = baker.make('event.Event', description="foo")
        event_ticket1 = baker.make('event.Ticket', event=event, quantity=10, price=100)

        self.order = baker.make('order.Order', emailAddress="me@gmail.com")

        with self.settings(EVENTLINEZ_FEE=0.10):
            order_item1 = OrderItem(event_ticket=event_ticket1, quantity=1,
                                    unit_price=100, amount=100, fee=10, order=self.order)
            order_item2 = OrderItem(event_ticket=event_ticket1, quantity=1,
                                    unit_price=100, amount=100, fee=10, order=self.order)
            order_item1.save()
            order_item2.save()

        self.order.send_notification()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].to, [self.order.emailAddress])
        self.assertEqual(mail.outbox[0].subject, "Eventlinez - New Order #" + str(self.order.id))


class OrderTicketGeneration(TestCase):

    def test_create_order_item_should_create_a_ticket(self):
        event = baker.make('event.Event', description="foo", unit_price=100)
        event_ticket = baker.make('event.Ticket', event=event, quantity=10, price=100)
        order = baker.make('order.Order')

        with self.settings(EVENTLINEZ_FEE=0.10):
            order_item1 = OrderItem(quantity=2, unit_price=50, amount=100,
                                    fee=10,  order=order, event_ticket=event_ticket)
            order_item1.save()

        self.assertEqual(Ticket.objects.count(), 2)

    def test_create_order_should_decrease_ticket_quantity(self):
        event = baker.make('event.Event', description="foo", unit_price=50)
        order = baker.make('order.Order')

        with self.settings(EVENTLINEZ_FEE=0.10):
            order_item1 = OrderItem(quantity=1, unit_price=100,  amount=100, fee=10, order=order, event=event)
            order_item1.save()

        event.refresh_from_db()
        self.assertEqual(event.stock, 0)
