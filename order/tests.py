from django.test import TestCase
from django.core import mail
from django.conf import settings

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
            shippingPostcode="60326901"
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