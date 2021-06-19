from django.test import TestCase

from .models import CartItem, Cart
from event.models import Event
from event.models import Ticket
from model_bakery import baker
from django.urls import reverse


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


class CardAddTest(TestCase):

    def setUp(self):
        event = baker.make(Event, description="foo")
        self.camarote = baker.make(Ticket, event=event, quantity=10)
        self.frontstage = baker.make(Ticket, event=event, quantity=20)
        self.pista = baker.make(Ticket, event=event, quantity=40)

    def test_deve_adicionar_carrinho_da_sessacao(self):
        payload = {
            "promocode": None,
            "tickets": [
                {"id": self.camarote.id, "quantity": 1},
                {"id": self.frontstage.id, "quantity": 0},
                {"id": self.pista.id, "quantity": 0},
            ]
        }
        self.assertEqual(0, Cart.objects.filter(cart_id=self.client.session.session_key).count())
        self.client.post(reverse('cart:add_cart'), payload, 'application/json')
        self.assertEqual(1, Cart.objects.filter(cart_id=self.client.session.session_key).count(),
                         "Deve ser criado um carrinho associado a esta sessao")

    def test_deve_redirecionar_para_detalhamento_do_carrinho(self):
        payload = {
            "promocode": None,
            "tickets": [
                {"id": self.camarote.id, "quantity": 1},
                {"id": self.frontstage.id, "quantity": 0},
                {"id": self.pista.id, "quantity": 0},
            ]
        }
        response = self.client.post(reverse('cart:add_cart'), payload, 'application/json')
        self.assertRedirects(response, reverse('cart:detail'),
                             target_status_code=302, fetch_redirect_response=True)

    def test_nao_deve_add_ao_carrinho_se_quantidade_for_0(self):
        payload = {
            "promocode": None,
            "tickets": [
                {"id": self.camarote.id, "quantity": 0},
                {"id": self.frontstage.id, "quantity": 0},
                {"id": self.pista.id, "quantity": 0},
            ]
        }
        self.client.post(reverse('cart:add_cart'), payload, 'application/json')
        cart = Cart.objects.get(cart_id=self.client.session.session_key)
        self.assertEqual(0, cart.cartitem_set.count())

    def test_deve_dar_erro_se_add_ao_item_com_quantidade_menor_que_0(self):
        payload = {
            "promocode": None,
            "tickets": [
                {"id": self.camarote.id, "quantity": -1},
            ]
        }
        response = self.client.post(reverse('cart:add_cart'), payload, 'application/json')
        self.assertEqual(response.status_code, 400)
