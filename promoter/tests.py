from datetime import timedelta

from django.utils import timezone
from django.test import TestCase

from promoter.models import Promoter
from promoter.models import Event
from promoter.api import EventListAPIView
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

