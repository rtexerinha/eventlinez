from django.test import TestCase
from django.core.cache import cache
from model_bakery import baker
from datetime import datetime, timedelta
from django.urls import reverse
from django.test import Client


class EventsHomeView(TestCase):

    def setUp(self):
        cache.clear()

    def test_ordem_de_exibicao_dos_eventos(self):
        event1 = baker.make('event.Event', _create_files=True, description="foo",
                            available=True, event_date=datetime.now() + timedelta(weeks=-4))
        event2 = baker.make('event.Event', _create_files=True, description="foo",
                            available=True, event_date=datetime.now() + timedelta(days=-1))

        event3 = baker.make('event.Event', _create_files=True, description="foo",
                            available=True, event_date=datetime.now() + timedelta(days=1))
        event4 = baker.make('event.Event', _create_files=True, description="foo",
                            available=True, event_date=datetime.now() + timedelta(weeks=4))
        client = Client()
        response = client.get(reverse('index'))
        # When there are < 4 future events, they all go in events_all
        events_all = response.context[-1]['events_all']
        self.assertEqual(4, len(events_all))
        self.assertEqual(events_all[0], event3)
        self.assertEqual(events_all[1], event4)
        self.assertEqual(events_all[2], event2)
        self.assertEqual(events_all[3], event1)


class EventModel(TestCase):

    def test_evento_deve_ter_atributo_slug(self):
        event = baker.make('event.Event', name="Show do Milhao", description="foo")
        self.assertEqual('show-do-milhao', event.slug)

    def test_get_url(self):
        event1 = baker.make('event.Event', name="Show do Milhao", description="foo")
        url = event1.get_url()
        self.assertIsInstance(url, str)
