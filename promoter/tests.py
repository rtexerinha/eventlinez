import datetime
from datetime import timedelta
from datetime import date

from django.utils import timezone
from django.test import TestCase
from order.models import OrderItem

from promoter.models import Promoter
from promoter.models import Event
from promoter.api import EventListAPIView
from promoter.api import sales_report
from django.test import TestCase
from django.contrib.auth import get_user_model
from promoter.models import Promoter, Event
from order.models import Order, OrderItem
from event.models import Ticket, Category

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate


class SearchEventTest(TestCase):

    def setUp(self):
        User = get_user_model()
        user = User.objects.create_user(username='testuser', email='test@example.com')
        self.promoter = Promoter.objects.create(user=user, email='test@example.com')
        self.factory = APIRequestFactory()
        self.view = EventListAPIView.as_view()

    def test_filter_by_state(self):
        event1 = Event.objects.create(name="Event 1", description="foo", event_date=timezone.now() + timedelta(days=-4))
        event2 = Event.objects.create(name="Event 2", description="foo", event_date=timezone.now() + timedelta(days=-3))
        event3 = Event.objects.create(name="Event 3", description="foo", event_date=timezone.now() + timedelta(days=-2))
        event4 = Event.objects.create(name="Event 4", description="foo", event_date=timezone.now() + timedelta(days=-1, minutes=1))
        event5 = Event.objects.create(name="Event 5", description="foo", event_date=timezone.now() + timedelta(days=1))
        
        self.promoter.event_set.add(event1, event2, event3, event4, event5)

        request = self.factory.get('/promoter/api/event', data={"state": "previous"})
        force_authenticate(request, user=self.promoter.user)
        response = self.view(request)
        self.assertEqual(len(response.data), 3)

        request = self.factory.get('/promoter/api/event', data={"state": "current"})
        force_authenticate(request, user=self.promoter.user)
        response = self.view(request)
        self.assertEqual(len(response.data), 2)

    def test_filter_by_name(self):
        event1 = Event.objects.create(name="Beatles", description="foo")
        event2 = Event.objects.create(name="Rolling Stones", description="foo")
        self.promoter.event_set.add(event1, event2)

        request = self.factory.get('/promoter/api/event', data={"name": "Beatles"})
        force_authenticate(request, user=self.promoter.user)
        response = self.view(request)
        self.assertEqual(len(response.data), 1)


class TestSalesReportAPI(TestCase):
    def setUp(self):
        User = get_user_model()
        user = User.objects.create_user(username='testuser2', email='test2@example.com')
        self.promoter = Promoter.objects.create(user=user, email='test2@example.com')
        self.factory = APIRequestFactory()
        
        # Create a category
        category = Category.objects.create(name="Test Category", slug="test-category")
        
        self.event = Event.objects.create(
            name="Test Event", 
            description="foo",
            event_date=timezone.now() + timedelta(days=30),
            category=category,
            promoter=self.promoter
        )

        ticket_type = Ticket.objects.create(name="Test Ticket", event=self.event, price=50)

        order1 = Order.objects.create(
            emailAddress='test1@example.com',
            total=100,
            token='test_token_1'
        )
        order1.created = datetime.datetime(day=5, month=12, year=2022)
        order1.save()

        order2 = Order.objects.create(
            emailAddress='test2@example.com',
            total=100,
            token='test_token_2'
        )
        order2.created = timezone.now() - timedelta(days=60)  # 2 months ago
        order2.save()

        order3 = Order.objects.create(
            emailAddress='test3@example.com',
            total=100,
            token='test_token_3'
        )
        order3.created = timezone.now() - timedelta(days=1)  # 1 day ago (current month)
        order3.save()

        # baker.make(OrderItem, event_ticket=ticket_type, order=order, _quantity=2) Model Baker shitty bug
        OrderItem.objects.create(quantity=2, unit_price=50, fee=2, amount=100, order=order1, event_ticket=ticket_type)
        OrderItem.objects.create(quantity=3, unit_price=50, fee=2, amount=100, order=order1, event_ticket=ticket_type)
        OrderItem.objects.create(quantity=8, unit_price=50, fee=2, amount=100, order=order2, event_ticket=ticket_type)
        OrderItem.objects.create(quantity=8, unit_price=50, fee=2, amount=100, order=order3, event_ticket=ticket_type)
        OrderItem.objects.create(quantity=5, unit_price=50, fee=2, amount=100, order=order3, event_ticket=ticket_type)

    def test_sales_report_should_filter_by_event(self):
        # Create another category for this event
        another_category = Category.objects.create(name="Another Category", slug="another-category")
        another_event = Event.objects.create(
            name="Another Event", 
            description="another event",
            event_date=timezone.now() + timedelta(days=30),
            category=another_category,
            promoter=self.promoter
        )

        request = self.factory.get(f"/promoter/api/event/{another_event.id}/salesReport", data={"by": "month"})
        force_authenticate(request, user=self.promoter.user)
        response = sales_report(request, another_event.id)

        self.assertEqual(len(response.data["data"]), 0)

    def test_sales_by_day(self):
        request = self.factory.get(f"/promoter/api/event/{self.event.id}/salesReport", data={"by": "day"})
        force_authenticate(request, user=self.promoter.user)
        response = sales_report(request, self.event.id)

        self.assertEqual(len(response.data["data"]), 3)
        self.assertIsInstance(response.data["data"][0]["group"], date)

        self.assertEqual(response.data["data"][0]["value"], 5)
        self.assertEqual(response.data["data"][1]["value"], 8)
        self.assertEqual(response.data["data"][2]["value"], 13)

    def test_sales_by_month(self):
        request = self.factory.get(f"/promoter/api/event/{self.event.id}/salesReport", data={"by": "month"})
        force_authenticate(request, user=self.promoter.user)
        response = sales_report(request, self.event.id)

        # The test now expects 2 months since order2 and order3 are in the same month
        self.assertEqual(len(response.data["data"]), 2)
        self.assertEqual(response.data["data"][0]["group"], "Dec 22")

        self.assertEqual(response.data["data"][0]["value"], 5)  # Dec 22: 2+3=5
        self.assertEqual(response.data["data"][1]["value"], 21)  # Current month: 8+8+5=21


class TestUtil(TestCase):

    def test_transform_to_month(self):
        data = [{'month': 1, 'year': 2023, 'value': 250.0}, {'month': 12, 'year': 2022, 'value': 400.0}]
        from promoter.util import transform_month

        data = list(map(transform_month, data))
        self.assertEquals(data[0]["group"], "Jan 23")
        self.assertEquals(data[1]["group"], "Dec 22")
