from django.test import TestCase
from model_bakery import baker

from order.models import Order
from order.models import OrderItem
from .forms import EventForm
from .models import Event


class EventFormTest(TestCase):

    def test_quantidade_de_tickets_ofertados_nao_pode_ser_menor_que_a_quantidade_de_tickets_vendidos(self):
        event = baker.make(Event, description="foo", stock=10)
        order = baker.make(Order)
        OrderItem.objects.create(event=event, quantity=3, price=100, amount=100, fee=10, order=order)
        OrderItem.objects.create(event=event, quantity=3, price=100, amount=100, fee=10, order=order)

        self.assertEqual(4, event.sales_info()['qtd_available'])
        self.assertEqual(6, event.sales_info()['qtd_sould'])

        form = EventForm({"stock": 5}, instance=event)
        self.assertFalse(form.is_valid())
        self.assertEqual('Ticket quantity cannot be less than quantity sold', form.errors['stock'][0])
