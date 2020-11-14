from django.test import TestCase
from django.core import mail
from django.conf import settings

from .models import Order
from .models import OrderItem
from cart.views import send_email


class OrderMailTest(TestCase):

    def test_send_mail(self):
        order = Order(
            token="12",
            total=123, billingName="Rafael Reuber",
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
        order.save()
        order_item1 = OrderItem(event="Event 1", quantity=1, price=100, order=order)
        order_item2 = OrderItem(event="Event 2", quantity=1, price=50, order=order)

        order_item1.save()
        order_item2.save()

        send_email(order_id=order.id)
        self.assertEqual(1, len(mail.outbox))
        self.assertEqual(mail.outbox[0].to, [order.emailAddress])
        self.assertEqual(mail.outbox[0].subject, "Eventlinez - New Order #" + str(order.id))


class OrderItemTestCase(TestCase):

    def test_price_free_shold_work_when_fee_is_a_integer(self):
        settings.EVENTLINEZ_FEE = 10

