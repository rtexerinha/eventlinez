from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from promoter.core.permissions import IsDoorman
from promoter.models import Partner
from .models import Ticket
from .serializers import TicketSoldSerializers


class TicketSoldListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = Ticket

    def get_queryset(self):
        user = self.request.user
        event_id = self.request.query_params.get('event_id')
        guest_name = self.request.query_params.get('guest_name', None)

        if hasattr(user, 'promoter'):
            queryset = Ticket.objects.filter(event_ticket__event__promoter__user=user)
        else:
            queryset = Ticket.objects.filter(
                Q(event_ticket__event__partner__user=user, day_event__isnull=True) |
                Q(day_event__partner__user=user)
            )

        queryset = queryset.select_related('customer', 'order_item__order')

        if event_id:
            queryset = queryset.filter(
                Q(event_ticket__event__id=event_id) | Q(day_event__id=event_id)
            )

        if guest_name:
            queryset = queryset.filter(
                Q(guest_name__icontains=guest_name) |
                Q(customer__first_name__icontains=guest_name) |
                Q(customer__last_name__icontains=guest_name) |
                Q(customer__email__icontains=guest_name)
            )

        return queryset.order_by('customer__first_name', 'customer__last_name', 'guest_name')


class TicketSoldDetailsAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSoldSerializers
    model = Ticket

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']
        return self.model.objects.filter(event_ticket__event__promoter__user=user, id=pk)


class TicketSoldCheckinAPIView(APIView):
    """
    POST/PATCH /ticket/api/checkin/<pk>
    Manual check-in by ticket ID. Same pattern as DoormanManualCheckinAPIView.
    """
    permission_classes = [IsAuthenticated, IsDoorman]

    def patch(self, request, pk):
        return self.post(request, pk)

    def post(self, request, pk):
        try:
            ticket = Ticket.objects.select_related(
                'event_ticket__event__promoter', 'day_event', 'customer'
            ).get(pk=pk)
        except Ticket.DoesNotExist:
            return Response({'success': False, 'message': 'Ticket not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        effective_event = ticket.day_event if ticket.day_event else ticket.event_ticket.event

        user = request.user
        if not hasattr(user, 'promoter'):
            if not Partner.objects.filter(
                user=user, event=effective_event, role__in=['DOORMAN', 'PARTNER'], disable=False
            ).exists():
                return Response(
                    {'success': False, 'message': 'You are not assigned to this event.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif effective_event.promoter.user != user:
            return Response(
                {'success': False, 'message': 'This ticket does not belong to your event.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        deadline = effective_event.event_date + timedelta(hours=6)
        if timezone.now() > deadline:
            return Response(
                {'success': False, 'message': f'Check-in period has ended. Deadline was {deadline.strftime("%b %d %H:%M")}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                ticket = Ticket.objects.select_related('event_ticket', 'customer').select_for_update().get(pk=pk)

                if ticket.checkin_date:
                    return Response({
                        'success': False,
                        'message': 'This ticket has already been checked in.',
                        'already_checked_in': True,
                        'ticket_id': ticket.id,
                        'guest_name': ticket.guest_name or (
                            f"{ticket.customer.first_name} {ticket.customer.last_name}".strip()
                            if ticket.customer else ''
                        ) or 'Unknown',
                        'event_name': effective_event.name,
                        'ticket_type': ticket.event_ticket.name,
                        'first_checkin_at': ticket.checkin_date,
                        'checked_in_at': ticket.checkin_date,
                    })

                ticket.checkin_date = timezone.now()
                ticket.save(update_fields=['checkin_date'])
        except Exception as exc:
            import traceback, logging
            logging.getLogger(__name__).error(
                "TicketSoldCheckinAPIView FAILED: pk=%s user=%s error=%s\n%s",
                pk, request.user.username, exc, traceback.format_exc(),
            )
            return Response(
                {'success': False, 'message': 'Check-in failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            'success': True,
            'message': 'Check-in successful! Welcome!',
            'already_checked_in': False,
            'ticket_id': ticket.id,
            'guest_name': ticket.guest_name or (
                f"{ticket.customer.first_name} {ticket.customer.last_name}".strip()
                if ticket.customer else ''
            ) or 'Unknown',
            'event_name': effective_event.name,
            'ticket_type': ticket.event_ticket.name,
            'checked_in_at': ticket.checkin_date,
            'first_checkin_at': None,
        })


class TicketSoldCheckinQrcodeAPIView(APIView):
    """
    POST/PATCH /ticket/api/checkin/qrcode/<uuid>
    QR scan check-in by UUID. Same pattern as DoormanScanPaidTicketAPIView.
    """
    permission_classes = [IsAuthenticated, IsDoorman]

    def patch(self, request, uuid):
        return self.post(request, uuid)

    def post(self, request, uuid):
        try:
            ticket = Ticket.objects.select_related(
                'event_ticket__event__promoter', 'day_event', 'customer',
            ).get(uuid=uuid)
        except (Ticket.DoesNotExist, ValueError, ValidationError):
            from ticket.models import CancelledTicket
            cancelled = CancelledTicket.objects.filter(uuid=uuid).first()
            if cancelled:
                reason_label = 'refunded' if cancelled.cancelled_reason == CancelledTicket.REASON_REFUNDED else 'cancelled'
                return Response(
                    {'success': False,
                     'message': f'This ticket has been {reason_label} and is no longer valid.',
                     'already_checked_in': False},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {'success': False, 'message': 'Ticket not found. Please check the QR code.', 'already_checked_in': False},
                status=status.HTTP_404_NOT_FOUND,
            )

        effective_event = ticket.day_event if ticket.day_event else ticket.event_ticket.event

        user = request.user
        if not hasattr(user, 'promoter'):
            if not Partner.objects.filter(
                user=user, event=effective_event, role__in=['DOORMAN', 'PARTNER'], disable=False
            ).exists():
                return Response(
                    {'success': False, 'message': 'You are not assigned to this event.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif effective_event.promoter.user != user:
            return Response(
                {'success': False, 'message': 'This ticket does not belong to your event.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        deadline = effective_event.event_date + timedelta(hours=6)
        if timezone.now() > deadline:
            return Response(
                {
                    'success': False,
                    'message': f'Check-in period has ended. Deadline was {deadline.strftime("%b %d %H:%M")}.',
                    'already_checked_in': False,
                    'event_name': effective_event.name,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                ticket = Ticket.objects.select_related('event_ticket', 'customer').select_for_update().get(pk=ticket.pk)

                if ticket.checkin_date:
                    return Response({
                        'success': False,
                        'message': 'This ticket has already been checked in.',
                        'already_checked_in': True,
                        'ticket_id': ticket.id,
                        'guest_name': ticket.guest_name or (
                            f"{ticket.customer.first_name} {ticket.customer.last_name}".strip()
                            if ticket.customer else ''
                        ) or 'Unknown',
                        'event_name': effective_event.name,
                        'ticket_type': ticket.event_ticket.name,
                        'first_checkin_at': ticket.checkin_date,
                        'checked_in_at': ticket.checkin_date,
                    })

                ticket.checkin_date = timezone.now()
                ticket.save(update_fields=['checkin_date'])
        except Exception as exc:
            import traceback, logging
            logging.getLogger(__name__).error(
                "TicketSoldCheckinQrcodeAPIView FAILED: uuid=%s user=%s error=%s\n%s",
                uuid, request.user.username, exc, traceback.format_exc(),
            )
            return Response(
                {'success': False, 'message': 'Check-in failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            'success': True,
            'message': 'Check-in successful! Welcome!',
            'already_checked_in': False,
            'ticket_id': ticket.id,
            'guest_name': ticket.guest_name or (
                f"{ticket.customer.first_name} {ticket.customer.last_name}".strip()
                if ticket.customer else ''
            ) or 'Unknown',
            'event_name': effective_event.name,
            'ticket_type': ticket.event_ticket.name,
            'checked_in_at': ticket.checkin_date,
            'first_checkin_at': None,
        })
