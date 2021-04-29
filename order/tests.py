from django.test import TestCase
from django.core import mail
from model_bakery import baker

from .models import Order
from event.models import Ticket
from .models import OrderItem


class OrderModel(TestCase):

    def test_ticket_qty(self):
        event = baker.make('event.Event', description="foo", stock=10, unit_price=100)
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        order_item1 = OrderItem(event=event, quantity=1, price=100, amount=100, fee=10, order=order)
        order_item2 = OrderItem(event=event, quantity=3, price=100, amount=100, fee=10, order=order)
        order_item1.save()
        order_item2.save()

        self.assertEqual(order.ticket_qty(), 4)

    def test_ticket_qty_com_ordem_sem_linha(self):
        event = baker.make('event.Event', description="foo", stock=10, unit_price=100)
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        self.assertEqual(order.ticket_qty(), 0)

    def test_guest_name_deve_ser_o_customer_quando_uma_ordem_tiver_apenas_um_ticket(self):
        event = baker.make('event.Event', description="foo")
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        item1 = baker.make(OrderItem, event=event, quantity=1, order=order)

        tiket1 = Ticket.objects.get(order_item=item1)
        self.assertEqual(tiket1.guest_name, order.customer.first_name + " " + order.customer.last_name)

        event2 = baker.make('event.Event', description="foo2")
        event3 = baker.make('event.Event', description="foo3")
        order2 = baker.make('order.Order', emailAddress="me@gmail.com")
        item1 = baker.make(OrderItem, event=event2, quantity=1, order=order2)
        item2 = baker.make(OrderItem, event=event3, quantity=1, order=order2)

        tiket1 = Ticket.objects.get(order_item=item1)
        tiket2 = Ticket.objects.get(order_item=item2)
        self.assertEqual(tiket1.guest_name, order2.customer.first_name + " " + order2.customer.last_name)
        self.assertEqual(tiket2.guest_name, order2.customer.first_name + " " + order2.customer.last_name)


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
