from django.test import TestCase
from model_bakery import baker

from order.models import Order
from order.models import OrderItem
from .forms import EventForm
from .models import Event
from .models import Ticket as EventTicket


class EventFormTest(TestCase):

    def test_cria_novo_evento_nao_deve_validar_saldo_de_estoque_de_tickets(self):
        event = baker.make(Event, description="foo")
        form = EventForm(instance=event)
        self.assertTrue(form.is_valid())
        form.save()


class EventTicketTest(TestCase):

    def setUp(self):
        event = baker.make(Event, description="foo")
        self.camarote = baker.make(EventTicket, name="Camarote", event=event, quantity=10)
        self.frontstage = baker.make(EventTicket, name="Camarote", event=event, quantity=20)
        self.pista = baker.make(EventTicket, name="Camarote", event=event, quantity=40)

    def test_qty_available(self):
        self.assertEqual(self.camarote.qty_available(), 10)
        self.assertEqual(self.frontstage.qty_available(), 20)
        self.assertEqual(self.pista.qty_available(), 40)

        order = baker.make('order.Order', emailAddress="me@gmail.com")
        baker.make(OrderItem, event_ticket=self.camarote, quantity=1, order=order)
        baker.make(OrderItem, event_ticket=self.frontstage, quantity=1, order=order)
        baker.make(OrderItem, event_ticket=self.pista, quantity=1, order=order)

        self.assertEqual(self.camarote.qty_available(), 9)
        self.assertEqual(self.frontstage.qty_available(), 19)
        self.assertEqual(self.pista.qty_available(), 39)

        from ticket.models import Ticket
        self.assertEqual(3, Ticket.objects.count())

    def test_qty_sould(self):
        self.assertEqual(self.camarote.qty_sold(), 0)
        self.assertEqual(self.frontstage.qty_sold(), 0)
        self.assertEqual(self.pista.qty_sold(), 0)

        order = baker.make('order.Order', emailAddress="me@gmail.com")
        baker.make(OrderItem, event_ticket=self.camarote, quantity=1, order=order)
        baker.make(OrderItem, event_ticket=self.frontstage, quantity=1, order=order)
        baker.make(OrderItem, event_ticket=self.pista, quantity=1, order=order)

        self.assertEqual(self.camarote.qty_sold(), 1)
        self.assertEqual(self.frontstage.qty_sold(), 1)
        self.assertEqual(self.pista.qty_sold(), 1)

        from ticket.models import Ticket
        self.assertEqual(3, Ticket.objects.count())
