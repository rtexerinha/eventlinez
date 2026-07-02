import json
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from .models import Order, OrderItem, OrderEmailLog
from ticket.models import Ticket
from .views import _rebuild_order_from_stripe


class OrderModel(TestCase):

    def setUp(self):
        event = baker.make('event.Event', description="foo", available=False)
        self.event_ticket1 = baker.make('event.Ticket', event=event, quantity=10, price=100)
        self.event_ticket2 = baker.make('event.Ticket', event=event, quantity=5, price=200)

    def test_ticket_qty(self):
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        baker.make(OrderItem, event_ticket=self.event_ticket1, quantity=1, order=order)
        baker.make(OrderItem, event_ticket=self.event_ticket1, quantity=3, order=order)
        self.assertEqual(order.ticket_qty(), 4)

    def test_ticket_qty_com_ordem_sem_linha(self):
        baker.make('event.Event', description="foo")
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        self.assertEqual(order.ticket_qty(), 0)

    def test_guest_name_deve_ser_o_customer_quando_uma_ordem_tiver_apenas_um_ticket(self):
        order = baker.make('order.Order', emailAddress="me@gmail.com")
        item1 = baker.make(OrderItem, event_ticket=self.event_ticket1, quantity=1, order=order)

        tiket1 = Ticket.objects.get(order_item=item1)
        self.assertEqual(tiket1.guest_name, order.customer.first_name + " " + order.customer.last_name)

        event2 = baker.make('event.Event', description="foo2", available=False)
        event3 = baker.make('event.Event', description="foo3", available=False)
        order2 = baker.make('order.Order', emailAddress="me@gmail.com")
        item1 = baker.make(OrderItem, event_ticket=self.event_ticket1, quantity=1, order=order2)
        item2 = baker.make(OrderItem, event_ticket=self.event_ticket2, quantity=1, order=order2)

        tiket1 = Ticket.objects.get(order_item=item1)
        tiket2 = Ticket.objects.get(order_item=item2)
        self.assertEqual(tiket1.guest_name, order2.customer.first_name + " " + order2.customer.last_name)
        self.assertEqual(tiket2.guest_name, order2.customer.first_name + " " + order2.customer.last_name)


class OrderMailTest(TestCase):

    def test_send_mail(self):
        event = baker.make('event.Event', description="foo", available=False)
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
        event = baker.make('event.Event', description="foo", available=False)
        event_ticket = baker.make('event.Ticket', event=event, quantity=10, price=100)
        order = baker.make('order.Order')

        with self.settings(EVENTLINEZ_FEE=0.10):
            order_item1 = OrderItem(quantity=2, unit_price=50, amount=100,
                                    fee=10,  order=order, event_ticket=event_ticket)
            order_item1.save()

        self.assertEqual(Ticket.objects.count(), 2)

    def test_create_order_should_decrease_ticket_quantity(self):
        event = baker.make('event.Event', description="foo", available=False)
        event_ticket = baker.make('event.Ticket', event=event, quantity=1)
        order = baker.make('order.Order')

        with self.settings(EVENTLINEZ_FEE=0.10):
            order_item1 = OrderItem(quantity=1, unit_price=100,  amount=100, fee=10, order=order, event_ticket=event_ticket)
            order_item1.save()

        event.refresh_from_db()
        self.assertEqual(event_ticket.qty_available(), 0)


@override_settings(EVENTLINEZ_FEE=0.12)
class RebuildOrderFromStripeTest(TestCase):
    """Fix #2: rebuild a paid order from the Stripe metadata snapshot when the
    live cart is gone/empty but Stripe confirms payment."""

    def setUp(self):
        self.user = User.objects.create_user('john', 'john@example.com', 'pw')
        self.customer = baker.make(
            'customer.Customer', user=self.user, email='john@example.com',
            first_name='John', last_name='Doe',
        )
        event = baker.make('event.Event', description="foo", available=False)
        self.ticket = baker.make('event.Ticket', event=event, quantity=10, price=10)

    def _snapshot_metadata(self, qty=2):
        return {'cart_items_json': json.dumps([
            {'t': self.ticket.id, 'q': qty, 'v': None, 'p': None}
        ])}

    @patch('order.views.send_mail')
    def test_rebuild_creates_order_from_snapshot(self, _mock_mail):
        # amount_total in cents: 2 tickets @ $10 + 12% fee = $22.40
        order = _rebuild_order_from_stripe(
            session_id='cs_test_1', payment_intent='pi_1', amount_total=2240,
            metadata=self._snapshot_metadata(qty=2), customer=self.customer,
            cart=None, source='test',
        )
        self.assertIsNotNone(order)
        self.assertEqual(order.token, 'cs_test_1')
        self.assertEqual(order.payment_code, 'pi_1')
        self.assertEqual(order.total, Decimal('22.40'))
        self.assertEqual(order.orderitem_set.count(), 1)
        item = order.orderitem_set.first()
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.event_ticket_id, self.ticket.id)
        # Tickets are generated via the OrderItem post_save signal
        self.assertEqual(Ticket.objects.filter(order_item=item).count(), 2)

    @patch('order.views.send_mail')
    def test_rebuild_is_idempotent_on_session_id(self, _mock_mail):
        kwargs = dict(
            session_id='cs_dup', payment_intent='pi_2', amount_total=1120,
            metadata=self._snapshot_metadata(qty=1), customer=self.customer,
            cart=None, source='test',
        )
        first = _rebuild_order_from_stripe(**kwargs)
        second = _rebuild_order_from_stripe(**kwargs)
        self.assertEqual(first.id, second.id)
        self.assertEqual(Order.objects.filter(token='cs_dup').count(), 1)

    @patch('order.views.send_mail')
    def test_rebuild_returns_none_without_snapshot(self, _mock_mail):
        order = _rebuild_order_from_stripe(
            session_id='cs_nosnap', payment_intent='', amount_total=1000,
            metadata={}, customer=self.customer, cart=None, source='test',
        )
        self.assertIsNone(order)
        self.assertEqual(Order.objects.filter(token='cs_nosnap').count(), 0)

    @patch('order.views.send_mail')
    def test_rebuild_returns_none_when_snapshot_ticket_gone(self, _mock_mail):
        metadata = {'cart_items_json': json.dumps([{'t': 999999, 'q': 1, 'v': None, 'p': None}])}
        order = _rebuild_order_from_stripe(
            session_id='cs_goneticket', payment_intent='', amount_total=1000,
            metadata=metadata, customer=self.customer, cart=None, source='test',
        )
        self.assertIsNone(order)
        # No partial order should be left behind
        self.assertEqual(Order.objects.filter(token='cs_goneticket').count(), 0)


# ── OrderEmailLog ─────────────────────────────────────────────────────────────

class OrderEmailLogModelTest(TestCase):

    def _make_order(self):
        event = baker.make('event.Event', description='x', available=False)
        baker.make('event.Ticket', event=event, quantity=10, price=10)
        return baker.make('order.Order', emailAddress='test@example.com')

    def test_needs_resend_false_when_just_sent(self):
        order = self._make_order()
        log = OrderEmailLog.objects.create(order=order, email_to=order.emailAddress,
                                           sent_at=timezone.now())
        self.assertFalse(log.needs_resend)

    def test_needs_resend_true_after_two_hours(self):
        order = self._make_order()
        sent = timezone.now() - timezone.timedelta(hours=3)
        log = OrderEmailLog.objects.create(order=order, email_to=order.emailAddress,
                                           sent_at=sent)
        self.assertTrue(log.needs_resend)

    def test_needs_resend_false_when_delivered(self):
        order = self._make_order()
        sent = timezone.now() - timezone.timedelta(hours=3)
        log = OrderEmailLog.objects.create(order=order, email_to=order.emailAddress,
                                           sent_at=sent, delivered_at=timezone.now())
        self.assertFalse(log.needs_resend)

    def test_needs_resend_false_when_bounced(self):
        order = self._make_order()
        sent = timezone.now() - timezone.timedelta(hours=3)
        log = OrderEmailLog.objects.create(order=order, email_to=order.emailAddress,
                                           sent_at=sent, bounced=True)
        self.assertFalse(log.needs_resend)

    def test_needs_resend_false_when_already_resent(self):
        order = self._make_order()
        sent = timezone.now() - timezone.timedelta(hours=3)
        log = OrderEmailLog.objects.create(order=order, email_to=order.emailAddress,
                                           sent_at=sent, resent_at=timezone.now())
        self.assertFalse(log.needs_resend)


class SendNotificationLogsEmailTest(TestCase):

    def setUp(self):
        event = baker.make('event.Event', description='x', available=False)
        ticket = baker.make('event.Ticket', event=event, quantity=10, price=50)
        self.order = baker.make('order.Order', emailAddress='customer@example.com')
        item = OrderItem(event_ticket=ticket, quantity=1, unit_price=50,
                         amount=50, fee=5, order=self.order)
        item.save()

    def test_send_notification_creates_email_log(self):
        self.order.send_notification()
        log = OrderEmailLog.objects.filter(order=self.order).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.email_to, self.order.emailAddress)
        self.assertIsNotNone(log.sent_at)
        self.assertIsNone(log.resent_at)

    def test_send_notification_resend_stamps_resent_at(self):
        self.order.send_notification()
        self.order.send_notification(is_resend=True)
        log = OrderEmailLog.objects.get(order=self.order)
        self.assertIsNotNone(log.resent_at)
        self.assertIsNone(log.delivered_at)


# ── SendGrid webhook ──────────────────────────────────────────────────────────

class SendGridWebhookTest(TestCase):

    def setUp(self):
        self.url = reverse('order:sendgrid_webhook')
        event = baker.make('event.Event', description='x', available=False)
        baker.make('event.Ticket', event=event, quantity=5, price=25)
        self.order = baker.make('order.Order', emailAddress='buyer@example.com')
        self.log = OrderEmailLog.objects.create(
            order=self.order,
            email_to='buyer@example.com',
            sent_at=timezone.now(),
        )

    def _post(self, events):
        return self.client.post(
            self.url,
            data=json.dumps(events),
            content_type='application/json',
        )

    def test_get_returns_405(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 405)

    def test_delivered_event_sets_delivered_at(self):
        r = self._post([{'event': 'delivered', 'email': 'buyer@example.com'}])
        self.assertEqual(r.status_code, 200)
        self.log.refresh_from_db()
        self.assertIsNotNone(self.log.delivered_at)
        self.assertFalse(self.log.bounced)

    def test_bounce_event_sets_bounced(self):
        r = self._post([{'event': 'bounce', 'email': 'buyer@example.com',
                          'reason': 'user unknown'}])
        self.assertEqual(r.status_code, 200)
        self.log.refresh_from_db()
        self.assertTrue(self.log.bounced)
        self.assertEqual(self.log.bounce_reason, 'user unknown')

    def test_dropped_event_sets_bounced(self):
        r = self._post([{'event': 'dropped', 'email': 'buyer@example.com',
                          'reason': 'unsubscribed address'}])
        self.assertEqual(r.status_code, 200)
        self.log.refresh_from_db()
        self.assertTrue(self.log.bounced)

    def test_unknown_event_type_is_ignored(self):
        r = self._post([{'event': 'open', 'email': 'buyer@example.com'}])
        self.assertEqual(r.status_code, 200)
        self.log.refresh_from_db()
        self.assertIsNone(self.log.delivered_at)
        self.assertFalse(self.log.bounced)

    def test_invalid_json_returns_400(self):
        r = self.client.post(self.url, data='not-json',
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)

    def test_unknown_email_is_silently_ignored(self):
        r = self._post([{'event': 'delivered', 'email': 'nobody@example.com'}])
        self.assertEqual(r.status_code, 200)


# ── resend_undelivered_emails management command ──────────────────────────────

class ResendUndeliveredEmailsCommandTest(TestCase):

    def _make_log(self, sent_hours_ago, delivered=False, bounced=False, resent=False):
        event = baker.make('event.Event', description='x', available=False)
        ticket = baker.make('event.Ticket', event=event, quantity=10, price=20)
        order = baker.make('order.Order', emailAddress='x@example.com')
        item = OrderItem(event_ticket=ticket, quantity=1, unit_price=20,
                         amount=20, fee=2, order=order)
        item.save()
        sent_at = timezone.now() - timezone.timedelta(hours=sent_hours_ago)
        return OrderEmailLog.objects.create(
            order=order, email_to=order.emailAddress, sent_at=sent_at,
            delivered_at=timezone.now() if delivered else None,
            bounced=bounced,
            resent_at=timezone.now() if resent else None,
        )

    def _call(self, dry_run=False):
        from django.core.management import call_command
        out = StringIO()
        kwargs = {'stdout': out}
        if dry_run:
            kwargs['dry_run'] = True
        call_command('resend_undelivered_emails', **kwargs)
        return out.getvalue()

    def test_resends_undelivered_after_two_hours(self):
        log = self._make_log(sent_hours_ago=3)
        self._call()
        log.refresh_from_db()
        self.assertIsNotNone(log.resent_at)

    def test_does_not_resend_if_delivered(self):
        self._make_log(sent_hours_ago=3, delivered=True)
        self.assertIn('No undelivered emails found', self._call())

    def test_does_not_resend_if_bounced(self):
        self._make_log(sent_hours_ago=3, bounced=True)
        self.assertIn('No undelivered emails found', self._call())

    def test_does_not_resend_if_already_resent(self):
        self._make_log(sent_hours_ago=3, resent=True)
        self.assertIn('No undelivered emails found', self._call())

    def test_does_not_resend_if_less_than_two_hours(self):
        self._make_log(sent_hours_ago=1)
        self.assertIn('No undelivered emails found', self._call())

    def test_dry_run_does_not_stamp_resent_at(self):
        log = self._make_log(sent_hours_ago=3)
        self._call(dry_run=True)
        log.refresh_from_db()
        self.assertIsNone(log.resent_at)
