import io

from PyPDF2 import PdfReader
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from order.models import OrderItem
from datetime import datetime


class TicketTest(TestCase):

    def setUp(self) -> None:
        self.event_date = timezone.make_aware(datetime(year=2023, month=3, day=31, hour=23))

        ticket_type = baker.make("event.Ticket", event__description="foo", event__event_date=self.event_date, event__available=False)
        order = baker.make("order.Order")
        order_item = OrderItem.objects.create(order=order, quantity=2, unit_price=50, fee=2, amount=100,
                                              event_ticket=ticket_type)
        self.ticket = order_item.ticket_set.first()

    def test_ticket_pdf(self):
        pdf = self.ticket.as_pdf()

        reader = PdfReader(io.BytesIO(pdf))
        text = reader.pages[0].extract_text()
        lines = text.split("\n")

        self.assertEqual(lines[2], str(self.event_date.day))
        self.assertEqual(lines[3], "March 2023")
        self.assertEqual(lines[4], "23:00")
