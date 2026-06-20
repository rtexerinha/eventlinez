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

        deadline = effective_event.event_date + timedelta(hours=12)
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

        deadline = effective_event.event_date + timedelta(hours=12)
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


class TicketResendEmailAPIView(APIView):
    """
    POST /ticket/api/<pk>/resend/
    Resend the ticket PDF by email.
    Body: { "email": "override@example.com" }  (optional — defaults to buyer's email)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from django.conf import settings
        from django.core.mail import EmailMessage

        try:
            ticket = Ticket.objects.select_related(
                'order_item__order', 'event_ticket__event__promoter'
            ).get(pk=pk, event_ticket__event__promoter__user=request.user)
        except Ticket.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        target_email = request.data.get('email') or ticket.order_item.order.emailAddress
        if not target_email:
            return Response({'error': 'No email address available.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            pdf = ticket.as_pdf()
            event = ticket.event_ticket.event
            subject = f'Your ticket – {event.name}'
            body = (
                f'Hi,\n\nHere is your ticket for {event.name}.\n\n'
                f'Order: #{ticket.order_item.order.id}\n'
                f'Ticket type: {ticket.event_ticket.name}\n\n'
                f'Show the QR code attached (or at https://www.eventlinez.com/ticket/{ticket.uuid}) '
                f'at the entrance to check in.\n\nSee you there!'
            )
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@eventlinez.com'),
                to=[target_email],
            )
            email.attach(f'ticket_{ticket.id}.pdf', pdf, 'application/pdf')
            email.send()
            return Response({'success': True, 'message': f'Ticket sent to {target_email}.'})
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('TicketResendEmailAPIView error pk=%s: %s', pk, e)
            return Response({'success': False, 'error': 'Failed to send email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
