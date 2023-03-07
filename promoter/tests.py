from datetime import timedelta
from datetime import date

from django.utils import timezone
from django.test import TestCase
from order.models import OrderItem

from promoter.models import Promoter
from promoter.models import Event
from promoter.api import EventListAPIView
from promoter.api import sales_report
from model_bakery import baker

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate


class SearchEventTest(TestCase):

    def setUp(self):
        self.promoter = baker.make(Promoter)
        self.factory = APIRequestFactory()
        self.view = EventListAPIView.as_view()

    def test_filter_by_state(self):
        self.promoter.event_set.add(
            baker.make(Event, description="foo", event_date=timezone.now() + timedelta(days=-4)))
        self.promoter.event_set.add(
            baker.make(Event, description="foo", event_date=timezone.now() + timedelta(days=-3)))
        self.promoter.event_set.add(
            baker.make(Event, description="foo", event_date=timezone.now() + timedelta(days=-2)))
        self.promoter.event_set.add(
            baker.make(Event, description="foo", event_date=timezone.now() + timedelta(days=-1, minutes=1)))
        self.promoter.event_set.add(
            baker.make(Event, description="foo", event_date=timezone.now() + timedelta(days=1)))

        request = self.factory.get('/promoter/api/event', data={"state": "previous"})
        force_authenticate(request, user=self.promoter.user)
        response = self.view(request)
        self.assertEqual(len(response.data), 3)

        request = self.factory.get('/promoter/api/event', data={"state": "current"})
        force_authenticate(request, user=self.promoter.user)
        response = self.view(request)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_name(self):
        self.promoter.event_set.add(baker.make(Event, name="Beatles", description="foo"))
        self.promoter.event_set.add(baker.make(Event, name="Rolling Stones", description="foo"))

        request = self.factory.get('/promoter/api/event', data={"name": "Beatles"})
        force_authenticate(request, user=self.promoter.user)
        response = self.view(request)
        self.assertEqual(len(response.data), 1)


class TestSalesReportAPI(TestCase):
    def setUp(self):
        self.promoter = baker.make(Promoter)
        self.factory = APIRequestFactory()
        self.event = baker.make('event.Event', description="foo")

        ticket_type = baker.make('event.Ticket', event=self.event)

        order1 = baker.make('order.Order')
        order1.created = timezone.now() - timedelta(days=60)
        order1.save()

        order2 = baker.make('order.Order')
        order2.created = timezone.now() - timedelta(days=30)
        order2.save()

        order3 = baker.make('order.Order')
        order3.created = timezone.now() - timedelta(days=1)
        order3.save()

        # baker.make(OrderItem, event_ticket=ticket_type, order=order, _quantity=2) Model Baker shitty bug
        OrderItem.objects.create(quantity=2, unit_price=50, fee=2, amount=100, order=order1, event_ticket=ticket_type)
        OrderItem.objects.create(quantity=3, unit_price=50, fee=2, amount=100, order=order1, event_ticket=ticket_type)
        OrderItem.objects.create(quantity=8, unit_price=50, fee=2, amount=100, order=order2, event_ticket=ticket_type)
        OrderItem.objects.create(quantity=8, unit_price=50, fee=2, amount=100, order=order3, event_ticket=ticket_type)
        OrderItem.objects.create(quantity=5, unit_price=50, fee=2, amount=100, order=order3, event_ticket=ticket_type)

    def test_sales_report_should_filter_by_event(self):
        anoter_event = baker.make('event.Event', description="another event")

        request = self.factory.get(f"/promoter/api/event/{anoter_event.id}/salesReport", data={"by": "month"})
        force_authenticate(request, user=self.promoter.user)
        response = sales_report(request, anoter_event.id)

        self.assertEqual(len(response.data["data"]), 0)

    def test_sales_by_day(self):
        request = self.factory.get(f"/promoter/api/event/{self.event.id}/salesReport", data={"by": "day"})
        force_authenticate(request, user=self.promoter.user)
        response = sales_report(request, self.event.id)

        self.assertEqual(len(response.data["data"]), 3)
        self.assertIsInstance(response.data["data"][0]["group"], date)

        self.assertEqual(response.data["data"][0]["value"], 250.00)
        self.assertEqual(response.data["data"][1]["value"], 400.00)
        self.assertEqual(response.data["data"][2]["value"], 650)

    def test_sales_by_month(self):
        request = self.factory.get(f"/promoter/api/event/{self.event.id}/salesReport", data={"by": "month"})
        force_authenticate(request, user=self.promoter.user)
        response = sales_report(request, self.event.id)

        self.assertEqual(len(response.data["data"]),  3)

        self.assertEqual(response.data["data"][0]["value"], 250.00)
        self.assertEqual(response.data["data"][1]["value"], 400.00)
        self.assertEqual(response.data["data"][2]["value"], 650)
