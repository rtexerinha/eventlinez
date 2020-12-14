from django.test import TestCase
from django.core import mail
from model_bakery import baker

from .models import Order
from .models import OrderItem


class OrderMailTest(TestCase):

    def setUp(self):
        self.order = Order(
            token="12",
            total=123,
            billingName="Rafael Reuber",
            emailAddress="rafaelreuber@gmail.com",
            billingAddress1="Rua A",
            billingCity="Fortaleza",
            billingPostcode="60326-901",
            shippingCountry="BR",
            shippingName="Rafael Reuber",
            shippingAddress1="Rua A",
            shippingCity="Fortaleza",
            shippingPostcode="60326901",
            payment_code="123"
        )
        self.order.save()
        order_item1 = OrderItem(event="Event 1", quantity=1, price=100, order=self.order)
        order_item2 = OrderItem(event="Event 2", quantity=1, price=50, order=self.order)

        order_item1.save()
        order_item2.save()

    def test_send_mail(self):
        self.order.send_notification()
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].to, [self.order.emailAddress])
        self.assertEqual(mail.outbox[0].subject, "Eventlinez - New Order #" + str(self.order.id))


class OrderTicketGeneration(TestCase):

    def test_create_order_item_shuld_create_a_ticket(self):
        event = baker.make('event.Event', description="foo")
        event.save()
        order = baker.make('order.Order')
        order.save()

        order_item1 = OrderItem(quantity=1, price=100, order=order, event=event)
        order_item1.save()

        from event.models import Ticket
        self.assertEqual(Ticket.objects.count(), 1)
