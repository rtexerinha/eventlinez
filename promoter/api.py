from datetime import timedelta

from django.db.models import F, Sum, Q
from django.db.models.functions import ExtractMonth, TruncDate, ExtractYear
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import (
    ListAPIView, CreateAPIView, UpdateAPIView,
    ListCreateAPIView, RetrieveAPIView, DestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from account.api import get_user_role
from event.models import Event, Ticket
from promoter.models import Partner, PromoCode
from .core.permissions import IsEventParticipant, IsDoorman, IsDoormanForEvent
from .serializers import (
    PromoterSerializer, CategoriaSerializers, TicketTypeSerializers,
    EventSerializer, EventListSerializer, PartnerSerializer,
    PartnerCreateSerializer, PromoCodeSerializer, PromoCodeValidateSerializer,
    ComplimentaryTicketSerializer, ComplimentaryTicketCreateSerializer,
    BulkGuestCreateSerializer,
    # Doorman
    DoormanEventSerializer, TicketScanResultSerializer,
    GuestScanResultSerializer, DoormanCheckinStatsSerializer,
)
from promoter.util import transform_month

# ── existing views ────────────────────────────────────────────────────────────

class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email
        })


class PromoterListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PromoterSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        return self.model.objects.filter(user=user)


class EventDetailsAPIView(ListAPIView):
    permission_classes = [IsAuthenticated, IsEventParticipant]
    serializer_class = EventListSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pk = self.kwargs['pk']

        is_promoter = Q(id=pk, promoter__user=user)
        is_partner = Q(id=pk, id__in=Partner.objects.filter(user=user, role="PARTNER").values_list('event_id', flat=True))

        queryset = self.model.objects.filter(is_promoter | is_partner)

        for event in queryset:
            event.role = get_user_role(user, event)

        return queryset

class EventCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializer
    model = Event


class EventListAPIView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventListSerializer
    model = Event

    def get_queryset(self):
        name = self.request.query_params.get('name')
        state = self.request.query_params.get("state")
        queryset = Event.objects.filter(
            Q(partner__user=self.request.user) | Q(promoter__user=self.request.user)).distinct()

        dt_reference = timezone.now() + timedelta(-1)

        if name:
            queryset = queryset.filter(name__icontains=name)
        if state == "previous":
            queryset = queryset.filter(event_date__lte=dt_reference)
        if state == "current":
            queryset = queryset.filter(event_date__gte=dt_reference)

        events = []

        for event in queryset:
            event.role = get_user_role(self.request.user, event)
            events.append(event)

        return events


class EventUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EventSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        return self.model.objects.filter(promoter__user=user)


class CategoryListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CategoriaSerializers
    model = serializer_class.Meta.model
    queryset = model.objects.all()


class TicketTypeAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketTypeSerializers


class TicketTypeUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketTypeSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        ticket_id = self.kwargs['pk']
        return self.model.objects.filter(id=ticket_id)


class TicketTypeListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketTypeSerializers
    model = serializer_class.Meta.model

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        queryset = self.model.objects.filter(event_id=event_id, sold_out=False)
        return queryset

class TicketSoldOutUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk, event__promoter__user=request.user)
            ticket.sold_out = request.data.get("sold_out", ticket.sold_out)
            ticket.save()
            return Response({"message": "Status atualizado com sucesso"}, status=status.HTTP_200_OK)
        except Ticket.DoesNotExist:
            return Response({"error": "Ticket não encontrado"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request, event_id):
    from order.models import OrderItem
    by = request.GET["by"]

    queryset = OrderItem.objects.filter(event_ticket__event_id=event_id)
    calc = Sum(F('quantity'))

    if by == "day":
        group = TruncDate('order__created')
        queryset = queryset .annotate(group=group) \
            .values("group").annotate(value=calc).order_by("group")
        data = list(queryset)
    elif by == "month":
        queryset = queryset.annotate(
                    month=ExtractMonth('order__created'),
                    year=ExtractYear('order__created')).\
            values("month", "year").annotate(value=calc).order_by("year", "month")
        data = list(map(transform_month, list(queryset)))
    else:
        return Response(status=400)

    return Response({"data": data})


class PartnerUpdateAPIView(UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnerSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        partner_id = self.kwargs['pk']
        return self.model.objects.filter(id=partner_id)


class PartnerCreateAPIView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnerCreateSerializer


class PartnerListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PartnerSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        query = self.model.objects.filter(event_id=event_id)
        return query

# ══════════════════════════════════════════════════════════════════════════════
#  PROMO CODE API
# ══════════════════════════════════════════════════════════════════════════════

class PromoCodeListCreateAPIView(APIView):
    """
    GET  /api/promo-codes/?event_id=<id>  – list promo codes for an event
    POST /api/promo-codes/                – create a new promo code
    Only the promoter who owns the event can access these.
    """
    permission_classes = [IsAuthenticated]

    def _get_promoter(self, request):
        if not hasattr(request.user, 'promoter'):
            return None
        return request.user.promoter

    def get(self, request):
        promoter = self._get_promoter(request)
        if not promoter:
            return Response({'error': 'You are not a promoter.'}, status=status.HTTP_403_FORBIDDEN)

        qs = PromoCode.objects.filter(promoter=promoter).select_related('event')
        event_id = request.query_params.get('event_id')
        if event_id:
            qs = qs.filter(event_id=event_id)

        serializer = PromoCodeSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        promoter = self._get_promoter(request)
        if not promoter:
            return Response({'error': 'You are not a promoter.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = PromoCodeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            promo = serializer.save()
            return Response(PromoCodeSerializer(promo, context={'request': request}).data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PromoCodeDetailAPIView(APIView):
    """
    GET    /api/promo-codes/<pk>/  – retrieve
    PATCH  /api/promo-codes/<pk>/  – partial update
    DELETE /api/promo-codes/<pk>/  – delete
    """
    permission_classes = [IsAuthenticated]

    def _get_promo(self, request, pk):
        try:
            return PromoCode.objects.get(pk=pk, promoter__user=request.user)
        except PromoCode.DoesNotExist:
            return None

    def get(self, request, pk):
        promo = self._get_promo(request, pk)
        if not promo:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(PromoCodeSerializer(promo, context={'request': request}).data)

    def patch(self, request, pk):
        promo = self._get_promo(request, pk)
        if not promo:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = PromoCodeSerializer(promo, data=request.data, partial=True,
                                         context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        promo = self._get_promo(request, pk)
        if not promo:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        promo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PromoCodeToggleAPIView(APIView):
    """
    POST /api/promo-codes/<pk>/toggle/  – activate / deactivate
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            promo = PromoCode.objects.get(pk=pk, promoter__user=request.user)
        except PromoCode.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        promo.is_active = not promo.is_active
        promo.save()
        return Response({
            'id': promo.id,
            'is_active': promo.is_active,
            'message': f"Promo code {'activated' if promo.is_active else 'deactivated'}."
        })


class PromoCodeValidateAPIView(APIView):
    """
    POST /api/promo-codes/validate/
    Public endpoint – mobile customers validate a code before checkout.
    Body: { "code": "SAVE10", "event_id": 5, "subtotal": "50.00" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PromoCodeValidateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        code = serializer.validated_data['code'].upper().strip()
        event_id = serializer.validated_data['event_id']
        subtotal = serializer.validated_data['subtotal']

        try:
            promo = PromoCode.objects.get(code=code, event_id=event_id)
        except PromoCode.DoesNotExist:
            return Response({'valid': False, 'error': 'Promo code not found for this event.'},
                            status=status.HTTP_404_NOT_FOUND)

        # Determine customer identity
        customer_email = ''
        if request.user.is_authenticated:
            customer_email = request.user.email or request.session.session_key or ''
        else:
            customer_email = request.session.session_key or ''

        can_use, message = promo.can_be_used_by_customer(customer_email)
        if not can_use:
            return Response({'valid': False, 'error': message}, status=status.HTTP_200_OK)

        discount_amount = promo.calculate_discount(subtotal)
        new_total = max(0, subtotal - discount_amount)

        return Response({
            'valid': True,
            'code': promo.code,
            'discount_type': promo.discount_type,
            'discount_value': str(promo.discount_value),
            'discount_display': promo.get_discount_display(),
            'discount_amount': str(discount_amount),
            'subtotal': str(subtotal),
            'new_total': str(new_total),
        })


# ══════════════════════════════════════════════════════════════════════════════
#  GUEST LIST API
# ══════════════════════════════════════════════════════════════════════════════

class GuestListAPIView(APIView):
    """
    GET  /api/guest-list/?event_id=<id>&status=<s>&search=<q>
         List all complimentary tickets for an event.
    POST /api/guest-list/
         Create a single complimentary ticket.
    Only the promoter who owns the event can access these.
    """
    permission_classes = [IsAuthenticated]

    def _require_promoter(self, request):
        if not hasattr(request.user, 'promoter'):
            return None
        return request.user.promoter

    def get(self, request):
        from ticket.models_complimentary import ComplimentaryTicket
        promoter = self._require_promoter(request)
        if not promoter:
            return Response({'error': 'You are not a promoter.'}, status=status.HTTP_403_FORBIDDEN)

        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response({'error': 'event_id query parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure event belongs to promoter
        try:
            Event.objects.get(pk=event_id, promoter=promoter)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        qs = ComplimentaryTicket.objects.filter(event_id=event_id)

        # Filters
        ticket_status = request.query_params.get('status')
        if ticket_status:
            qs = qs.filter(status=ticket_status.upper())

        search = request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(guest_name__icontains=search) |
                Q(guest_email__icontains=search)
            )

        ticket_type = request.query_params.get('ticket_type')
        if ticket_type:
            qs = qs.filter(ticket_type=ticket_type.upper())

        # Stats summary
        total = qs.count()
        stats = {
            'total': total,
            'pending': qs.filter(status='PENDING').count(),
            'sent': qs.filter(status='SENT').count(),
            'checked_in': qs.filter(status='CHECKED_IN').count(),
            'cancelled': qs.filter(status='CANCELLED').count(),
        }

        serializer = ComplimentaryTicketSerializer(qs, many=True)
        return Response({'stats': stats, 'guests': serializer.data})

    def post(self, request):
        promoter = self._require_promoter(request)
        if not promoter:
            return Response({'error': 'You are not a promoter.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ComplimentaryTicketCreateSerializer(data=request.data,
                                                         context={'request': request})
        if serializer.is_valid():
            ticket = serializer.save()
            return Response(ComplimentaryTicketSerializer(ticket).data,
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GuestBulkCreateAPIView(APIView):
    """
    POST /api/guest-list/bulk/
    Create multiple complimentary tickets at once.
    Body: { "event_id": 5, "ticket_type": "GUEST_LIST", "send_immediately": true,
            "guests": [{"name":"Ana","email":"ana@x.com","phone":""},...] }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from ticket.models_complimentary import ComplimentaryTicket
        from ticket.views_complimentary import send_complimentary_ticket_email

        if not hasattr(request.user, 'promoter'):
            return Response({'error': 'You are not a promoter.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BulkGuestCreateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        event = Event.objects.get(pk=data['event_id'])
        ticket_type = data['ticket_type']
        send_immediately = data['send_immediately']
        guests = data['guests']

        created, sent, failed = [], 0, []
        for g in guests:
            try:
                ticket = ComplimentaryTicket.objects.create(
                    event=event,
                    guest_name=g['name'],
                    guest_email=g['email'],
                    guest_phone=g.get('phone', ''),
                    ticket_type=ticket_type,
                    notes=g.get('notes', ''),
                    issued_by=request.user.promoter,
                )
                created.append(ticket)
                if send_immediately:
                    if send_complimentary_ticket_email(ticket):
                        ticket.mark_as_sent()
                        sent += 1
                    else:
                        failed.append(g['email'])
            except Exception as e:
                failed.append(f"{g.get('email', '?')}: {str(e)}")

        return Response({
            'created': len(created),
            'sent': sent,
            'failed': failed,
            'guests': ComplimentaryTicketSerializer(created, many=True).data,
        }, status=status.HTTP_201_CREATED)


class GuestDetailAPIView(APIView):
    """
    GET    /api/guest-list/<pk>/         – retrieve a guest ticket
    PATCH  /api/guest-list/<pk>/         – update guest info / notes
    DELETE /api/guest-list/<pk>/         – cancel (soft-delete) a ticket
    """
    permission_classes = [IsAuthenticated]

    def _get_ticket(self, request, pk):
        from ticket.models_complimentary import ComplimentaryTicket
        try:
            return ComplimentaryTicket.objects.get(pk=pk, event__promoter__user=request.user)
        except ComplimentaryTicket.DoesNotExist:
            return None

    def get(self, request, pk):
        ticket = self._get_ticket(request, pk)
        if not ticket:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ComplimentaryTicketSerializer(ticket).data)

    def patch(self, request, pk):
        ticket = self._get_ticket(request, pk)
        if not ticket:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        allowed = ('guest_name', 'guest_email', 'guest_phone', 'ticket_type', 'notes')
        for field in allowed:
            if field in request.data:
                setattr(ticket, field, request.data[field])
        ticket.save()
        return Response(ComplimentaryTicketSerializer(ticket).data)

    def delete(self, request, pk):
        ticket = self._get_ticket(request, pk)
        if not ticket:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if ticket.checkin_date:
            return Response({'error': 'Cannot cancel a ticket that has already been checked in.'},
                            status=status.HTTP_400_BAD_REQUEST)
        ticket.cancel()
        return Response({'message': f'Ticket for {ticket.guest_name} cancelled.'})


class GuestResendEmailAPIView(APIView):
    """
    POST /api/guest-list/<pk>/resend/
    Resend the complimentary ticket email to the guest.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from ticket.models_complimentary import ComplimentaryTicket
        from ticket.views_complimentary import send_complimentary_ticket_email

        try:
            ticket = ComplimentaryTicket.objects.get(pk=pk, event__promoter__user=request.user)
        except ComplimentaryTicket.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        if ticket.status == 'CANCELLED':
            return Response({'error': 'Cannot resend a cancelled ticket.'}, status=status.HTTP_400_BAD_REQUEST)

        if send_complimentary_ticket_email(ticket):
            ticket.mark_as_sent()
            return Response({'success': True, 'message': f'Ticket resent to {ticket.guest_email}.'})
        return Response({'success': False, 'error': 'Failed to send email.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GuestShareLinksAPIView(APIView):
    """
    GET /api/guest-list/<pk>/share/
    Returns WhatsApp, SMS and direct check-in URL for a guest ticket.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        import urllib.parse
        from ticket.models_complimentary import ComplimentaryTicket

        try:
            ticket = ComplimentaryTicket.objects.get(pk=pk, event__promoter__user=request.user)
        except ComplimentaryTicket.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # WhatsApp
        wa_message = (
            f"🎉 Your FREE Ticket for {ticket.event.name}\n\n"
            f"👤 Guest: {ticket.guest_name}\n"
            f"🎫 Type: {ticket.get_ticket_type_display()}\n"
            f"📅 Date: {ticket.event.event_date.strftime('%B %d, %Y at %I:%M %p')}\n"
            f"📍 Location: {ticket.event.address}, {ticket.event.city}\n\n"
            f"🔗 Your ticket: {ticket.qr_code_url}\n\n"
            f"Show this QR code at the entrance!"
        )
        encoded_wa = urllib.parse.quote(wa_message)
        if ticket.guest_phone:
            phone = ''.join(filter(str.isdigit, ticket.guest_phone))
            whatsapp_url = f"https://wa.me/{phone}?text={encoded_wa}"
        else:
            whatsapp_url = f"https://wa.me/?text={encoded_wa}"

        # SMS
        sms_message = (
            f"Your FREE ticket for {ticket.event.name}. "
            f"Show this at entrance: {ticket.qr_code_url}"
        )
        encoded_sms = urllib.parse.quote(sms_message)
        if ticket.guest_phone:
            phone = ''.join(filter(str.isdigit, ticket.guest_phone))
            sms_url = f"sms:{phone}?body={encoded_sms}"
        else:
            sms_url = f"sms:?body={encoded_sms}"

        return Response({
            'guest_name': ticket.guest_name,
            'guest_email': ticket.guest_email,
            'guest_phone': ticket.guest_phone,
            'qr_code_url': ticket.qr_code_url,
            'whatsapp_url': whatsapp_url,
            'sms_url': sms_url,
            'checkin_url': ticket.qr_code_url,
        })


class GuestCheckinAPIView(APIView):
    """
    POST /api/guest-list/checkin/<uuid>/
    Check in a guest by UUID. Accessible to promoters AND doormen (partners).
    No auth required so a QR scanner app can call it, but we verify by uuid.
    """
    permission_classes = [AllowAny]

    def post(self, request, uuid):
        from ticket.models_complimentary import ComplimentaryTicket

        try:
            ticket = ComplimentaryTicket.objects.select_related('event').get(uuid=uuid)
        except ComplimentaryTicket.DoesNotExist:
            return Response({'success': False, 'error': 'Ticket not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        if ticket.status == 'CANCELLED':
            return Response({'success': False, 'error': 'This ticket has been cancelled.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if ticket.checkin_date:
            return Response({
                'success': False,
                'error': 'Ticket already checked in.',
                'checked_in_at': ticket.checkin_date.isoformat(),
                'guest_name': ticket.guest_name,
                'event_name': ticket.event.name,
            }, status=status.HTTP_200_OK)

        success, message = ticket.check_in()
        return Response({
            'success': success,
            'message': message,
            'guest_name': ticket.guest_name,
            'ticket_type': ticket.get_ticket_type_display(),
            'event_name': ticket.event.name,
            'checked_in_at': ticket.checkin_date.isoformat() if ticket.checkin_date else None,
        })


# ══════════════════════════════════════════════════════════════════════════════
#  DOORMAN API
# ══════════════════════════════════════════════════════════════════════════════

class DoormanProfileAPIView(APIView):
    """
    GET /api/doorman/profile/
    Returns the authenticated user's doorman profile:
    their name, email, and the list of events they are assigned to as DOORMAN.
    Also works for promoters (they see all their own events).
    """
    permission_classes = [IsAuthenticated, IsDoorman]

    def get(self, request):
        user = request.user

        if hasattr(user, 'promoter'):
            # Promoter sees all their own events
            events = Event.objects.filter(promoter__user=user)
            role = 'PROMOTER'
            assignments = None
        else:
            # Doorman sees only assigned, active events
            assignments = Partner.objects.filter(
                user=user, role='DOORMAN', disable=False
            ).select_related('event')
            events = Event.objects.filter(
                id__in=assignments.values_list('event_id', flat=True)
            )
            role = 'DOORMAN'

        events_data = DoormanEventSerializer(events, many=True).data

        return Response({
            'id': user.id,
            'name': user.get_full_name() or user.username,
            'email': user.email,
            'role': role,
            'events': events_data,
        })


class DoormanEventListAPIView(APIView):
    """
    GET /api/doorman/events/
    Lists every event the doorman is currently assigned to,
    with live check-in counters.
    Optional query params:
      ?state=current  – only future/today events (default)
      ?state=all      – all events
    """
    permission_classes = [IsAuthenticated, IsDoorman]

    def get(self, request):
        user = request.user
        state = request.query_params.get('state', 'current')

        if hasattr(user, 'promoter'):
            qs = Event.objects.filter(promoter__user=user)
        else:
            assigned_ids = Partner.objects.filter(
                user=user, role='DOORMAN', disable=False
            ).values_list('event_id', flat=True)
            qs = Event.objects.filter(id__in=assigned_ids)

        if state == 'current':
            from datetime import timedelta
            cutoff = timezone.now() - timedelta(hours=12)
            qs = qs.filter(event_date__gte=cutoff)

        serializer = DoormanEventSerializer(qs.order_by('event_date'), many=True)
        return Response(serializer.data)


class DoormanCheckinStatsAPIView(APIView):
    """
    GET /api/doorman/events/<event_id>/stats/
    Live check-in dashboard statistics for a single event.
    Includes paid tickets + guest list counts and last 10 check-ins.
    """
    permission_classes = [IsAuthenticated, IsDoormanForEvent]

    def get(self, request, event_id):
        from ticket.models import Ticket as PaidTicket
        from ticket.models_complimentary import ComplimentaryTicket

        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Paid ticket stats
        paid_qs = PaidTicket.objects.filter(event_ticket__event=event)
        paid_total = paid_qs.count()
        paid_checked_in = paid_qs.filter(checkin_date__isnull=False).count()
        paid_pending = paid_total - paid_checked_in

        # Guest list stats
        guest_qs = ComplimentaryTicket.objects.filter(event=event).exclude(status='CANCELLED')
        guest_total = guest_qs.count()
        guest_checked_in = guest_qs.filter(status='CHECKED_IN').count()
        guest_pending = guest_total - guest_checked_in

        # Totals
        total_expected = paid_total + guest_total
        total_checked_in = paid_checked_in + guest_checked_in
        pct = round((total_checked_in / total_expected * 100) if total_expected else 0, 1)

        # Recent check-ins (last 10, both types merged by time)
        recent_paid = list(
            paid_qs.filter(checkin_date__isnull=False)
            .order_by('-checkin_date')[:10]
            .values('guest_name', 'checkin_date', 'event_ticket__name')
        )
        recent_guests = list(
            guest_qs.filter(status='CHECKED_IN')
            .order_by('-checkin_date')[:10]
            .values('guest_name', 'checkin_date', 'ticket_type')
        )

        recent = []
        for r in recent_paid:
            recent.append({
                'type': 'paid',
                'name': r['guest_name'] or '—',
                'ticket_type': r['event_ticket__name'],
                'checked_in_at': r['checkin_date'].isoformat() if r['checkin_date'] else None,
            })
        for r in recent_guests:
            recent.append({
                'type': 'guest',
                'name': r['guest_name'],
                'ticket_type': r['ticket_type'],
                'checked_in_at': r['checkin_date'].isoformat() if r['checkin_date'] else None,
            })

        # Sort merged list by most recent first, take top 10
        recent.sort(key=lambda x: x['checked_in_at'] or '', reverse=True)
        recent = recent[:10]

        data = {
            'event_id': event.id,
            'event_name': event.name,
            'paid_total': paid_total,
            'paid_checked_in': paid_checked_in,
            'paid_pending': paid_pending,
            'guest_total': guest_total,
            'guest_checked_in': guest_checked_in,
            'guest_pending': guest_pending,
            'total_expected': total_expected,
            'total_checked_in': total_checked_in,
            'checkin_percentage': pct,
            'recent_checkins': recent,
        }

        serializer = DoormanCheckinStatsSerializer(data)
        return Response(serializer.data)


class DoormanScanPaidTicketAPIView(APIView):
    """
    POST /api/doorman/scan/ticket/
    Scans a paid-ticket QR code UUID and checks the attendee in.

    Body: { "uuid": "<ticket-uuid>", "event_id": <int> }

    The event_id is used to verify the ticket belongs to an event
    the doorman is assigned to.
    """
    permission_classes = [IsAuthenticated, IsDoorman]

    def post(self, request):
        from datetime import timedelta
        from ticket.models import Ticket as PaidTicket

        uuid_str = request.data.get('uuid', '').strip()
        event_id = request.data.get('event_id')

        if not uuid_str:
            return Response({'success': False, 'message': 'uuid is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Fetch ticket
        try:
            ticket = PaidTicket.objects.select_related(
                'event_ticket__event', 'customer'
            ).get(uuid=uuid_str)
        except PaidTicket.DoesNotExist:
            return Response(
                TicketScanResultSerializer({
                    'success': False,
                    'message': 'Ticket not found. Please check the QR code.',
                    'already_checked_in': False,
                }).data,
                status=status.HTTP_404_NOT_FOUND,
            )

        event = ticket.event_ticket.event

        # Verify doorman has access to this event
        user = request.user
        if not hasattr(user, 'promoter'):
            has_access = Partner.objects.filter(
                user=user, event=event, role='DOORMAN', disable=False
            ).exists()
            if not has_access:
                return Response(
                    {'success': False, 'message': 'You are not assigned as a Doorman for this event.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        elif event.promoter.user != user:
            return Response(
                {'success': False, 'message': 'This ticket does not belong to your event.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check check-in deadline (event date + 6 hours)
        deadline = event.event_date + timedelta(hours=6)
        if timezone.now() > deadline:
            return Response(
                TicketScanResultSerializer({
                    'success': False,
                    'message': f'Check-in period has ended. Deadline was {deadline.strftime("%b %d %H:%M")}.',
                    'already_checked_in': False,
                    'event_name': event.name,
                }).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Already checked in?
        if (ticket.checkin_date):
            return Response(
                TicketScanResultSerializer({
                    'success': False,
                    'message': 'This ticket has already been checked in.',
                    'already_checked_in': True,
                    'ticket_id': ticket.id,
                    'guest_name': ticket.guest_name or str(ticket.customer),
                    'event_name': event.name,
                    'ticket_type': ticket.event_ticket.name,
                    'first_checkin_at': ticket.checkin_date,
                    'checked_in_at': ticket.checkin_date,
                }).data,
            )

        # Perform check-in
        ticket.checkin_date = timezone.now()
        ticket.save(update_fields=['checkin_date'])

        return Response(
            TicketScanResultSerializer({
                'success': True,
                'message': 'Check-in successful! Welcome!',
                'already_checked_in': False,
                'ticket_id': ticket.id,
                'guest_name': ticket.guest_name or str(ticket.customer),
                'event_name': event.name,
                'ticket_type': ticket.event_ticket.name,
                'checked_in_at': ticket.checkin_date,
                'first_checkin_at': None,
            }).data,
        )


class DoormanScanGuestTicketAPIView(APIView):
    """
    POST /api/doorman/scan/guest/
    Scans a complimentary (guest-list) ticket QR code and checks in the guest.

    Body: { "uuid": "<complimentary-ticket-uuid>", "event_id": <int> }
    """
    permission_classes = [IsAuthenticated, IsDoorman]

    def post(self, request):
        from ticket.models_complimentary import ComplimentaryTicket

        uuid_str = request.data.get('uuid', '').strip()

        if not uuid_str:
            return Response({'success': False, 'message': 'uuid is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = ComplimentaryTicket.objects.select_related('event').get(uuid=uuid_str)
        except ComplimentaryTicket.DoesNotExist:
            return Response(
                GuestScanResultSerializer({
                    'success': False,
                    'message': 'Guest ticket not found. Please check the QR code.',
                    'already_checked_in': False,
                }).data,
                status=status.HTTP_404_NOT_FOUND,
            )

        event = ticket.event
        user = request.user

        # Verify doorman has access to this event
        if not hasattr(user, 'promoter'):
            has_access = Partner.objects.filter(
                user=user, event=event, role='DOORMAN', disable=False
            ).exists()
            if not has_access:
                return Response(
                    {'success': False, 'message': 'You are not assigned as a Doorman for this event.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Cancelled ticket
        if ticket.status == 'CANCELLED':
            return Response(
                GuestScanResultSerializer({
                    'success': False,
                    'message': 'This guest ticket has been cancelled.',
                    'already_checked_in': False,
                    'guest_name': ticket.guest_name,
                    'event_name': event.name,
                    'ticket_type': ticket.get_ticket_type_display(),
                }).data,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Already checked in?
        if ticket.checkin_date:
            return Response(
                GuestScanResultSerializer({
                    'success': False,
                    'message': 'This guest ticket has already been checked in.',
                    'already_checked_in': True,
                    'guest_name': ticket.guest_name,
                    'event_name': event.name,
                    'ticket_type': ticket.get_ticket_type_display(),
                    'first_checkin_at': ticket.checkin_date,
                    'checked_in_at': ticket.checkin_date,
                }).data,
            )

        # Perform check-in
        success, message = ticket.check_in()

        return Response(
            GuestScanResultSerializer({
                'success': success,
                'message': 'Guest checked in successfully! Welcome!' if success else message,
                'already_checked_in': False,
                'guest_name': ticket.guest_name,
                'event_name': event.name,
                'ticket_type': ticket.get_ticket_type_display(),
                'checked_in_at': ticket.checkin_date,
                'first_checkin_at': None,
            }).data,
        )


class DoormanAssignAPIView(APIView):
    """
    POST /api/doorman/assign/
    Promoter-only: assign an existing user as a DOORMAN for an event.
    The user must already have an account (registered via the app).

    Body: { "email": "door@example.com", "event_id": 5 }

    DELETE /api/doorman/assign/<partner_id>/
    Promoter-only: remove / disable a doorman assignment.
    """
    permission_classes = [IsAuthenticated]

    def _require_promoter(self, request):
        if not hasattr(request.user, 'promoter'):
            return None
        return request.user.promoter

    def post(self, request):
        from django.contrib.auth.models import User as DjangoUser

        promoter = self._require_promoter(request)
        if not promoter:
            return Response({'error': 'Only promoters can assign doormen.'},
                            status=status.HTTP_403_FORBIDDEN)

        email = request.data.get('email', '').strip().lower()
        event_id = request.data.get('event_id')

        if not email or not event_id:
            return Response({'error': 'email and event_id are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Verify event belongs to this promoter
        try:
            event = Event.objects.get(pk=event_id, promoter=promoter)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found or does not belong to you.'},
                            status=status.HTTP_404_NOT_FOUND)

        # Verify user exists
        try:
            door_user = DjangoUser.objects.get(username=email)
        except DjangoUser.DoesNotExist:
            return Response(
                {'error': f'No account found for "{email}". The doorman must register first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent promoter from assigning themselves
        if door_user == request.user:
            return Response({'error': 'You cannot assign yourself as a doorman.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create or re-enable the partner record
        partner, created = Partner.objects.get_or_create(
            email=email,
            event=event,
            defaults={
                'user': door_user,
                'role': 'DOORMAN',
                'disable': False,
            }
        )

        if not created:
            if partner.role != 'DOORMAN':
                return Response(
                    {'error': f'This user is already assigned as {partner.get_role_display()} for this event.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if partner.disable:
                partner.disable = False
                partner.save(update_fields=['disable'])
                return Response({
                    'message': f'{email} has been re-enabled as a Doorman for "{event.name}".',
                    'partner_id': partner.id,
                    'created': False,
                })
            return Response(
                {'error': 'This user is already a Doorman for this event.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'message': f'{email} has been assigned as a Doorman for "{event.name}".',
            'partner_id': partner.id,
            'created': True,
        }, status=status.HTTP_201_CREATED)

    def delete(self, request, partner_id):
        promoter = self._require_promoter(request)
        if not promoter:
            return Response({'error': 'Only promoters can remove doormen.'},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            partner = Partner.objects.get(
                pk=partner_id,
                role='DOORMAN',
                event__promoter=promoter,
            )
        except Partner.DoesNotExist:
            return Response({'error': 'Doorman assignment not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        partner.disable = True
        partner.save(update_fields=['disable'])
        return Response({'message': f'Doorman {partner.email} has been disabled for "{partner.event.name}".'})


class DoormanListAPIView(APIView):
    """
    GET /api/doorman/list/?event_id=<id>
    Promoter-only: list all doormen assigned to an event.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'promoter'):
            return Response({'error': 'Only promoters can list doormen.'},
                            status=status.HTTP_403_FORBIDDEN)

        event_id = request.query_params.get('event_id')
        qs = Partner.objects.filter(
            event__promoter=request.user.promoter,
            role='DOORMAN',
        ).select_related('user', 'event')

        if event_id:
            qs = qs.filter(event_id=event_id)

        data = [
            {
                'partner_id': p.id,
                'email': p.email,
                'name': p.user.get_full_name() if p.user else p.email,
                'event_id': p.event.id,
                'event_name': p.event.name,
                'active': not p.disable,
                'assigned_at': p.created_at.isoformat(),
            }
            for p in qs
        ]
        return Response(data)


# ══════════════════════════════════════════════════════════════════════════════
#  EVENT DOORMEN API (for mobile app)
# ══════════════════════════════════════════════════════════════════════════════

class EventDoormenAPIView(APIView):
    """
    GET /api/event-doormen/?event_id=<id>
    Returns all doormen assigned to a specific event.
    Promoter-only endpoint.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'promoter'):
            return Response({'error': 'Only promoters can view event doormen.'},
                            status=status.HTTP_403_FORBIDDEN)

        event_id = request.query_params.get('event_id')
        if not event_id:
            return Response({'error': 'event_id query parameter is required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Verify event belongs to this promoter
        try:
            event = Event.objects.get(pk=event_id, promoter=request.user.promoter)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found or does not belong to you.'},
                            status=status.HTTP_404_NOT_FOUND)

        doormen = Partner.objects.filter(
            event_id=event_id,
            role='DOORMAN'
        ).select_related('user')

        result = [{
            'id': d.id,
            'user_id': d.user.id if d.user else None,
            'user_name': d.user.get_full_name() if d.user else d.email,
            'user_email': d.email,
            'assigned_at': d.created_at.isoformat(),
            'active': not d.disable,
        } for d in doormen]

        return Response(result)


class AvailableDoormenAPIView(APIView):
    """
    GET /api/available-doormen/?event_id=<id>
    Returns all users who have been assigned as doormen to ANY of the promoter's events,
    excluding those already assigned to the specified event.
    This helps promoters quickly re-assign doormen they've worked with before.
    
    Promoter-only endpoint.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.auth.models import User as DjangoUser

        if not hasattr(request.user, 'promoter'):
            return Response({'error': 'Only promoters can view available doormen.'},
                            status=status.HTTP_403_FORBIDDEN)

        event_id = request.query_params.get('event_id')
        
        # Get all users who have been doormen for this promoter's events
        promoter_events = Event.objects.filter(promoter=request.user.promoter)
        
        # Get all unique doorman emails from this promoter's events
        all_doormen = Partner.objects.filter(
            event__in=promoter_events,
            role='DOORMAN'
        ).select_related('user').values('email', 'user__id', 'user__first_name', 'user__last_name')

        # If event_id provided, exclude doormen already assigned to that event
        if event_id:
            assigned_emails = Partner.objects.filter(
                event_id=event_id,
                role='DOORMAN',
                disable=False
            ).values_list('email', flat=True)
            
            all_doormen = all_doormen.exclude(email__in=assigned_emails)

        # Remove duplicates and build response
        seen_emails = set()
        result = []
        for d in all_doormen:
            if d['email'] not in seen_emails:
                seen_emails.add(d['email'])
                name = f"{d['user__first_name'] or ''} {d['user__last_name'] or ''}".strip()
                result.append({
                    'id': d['user__id'],
                    'name': name if name else d['email'],
                    'email': d['email']
                })

        return Response(result)


class SearchUsersForDoormanAPIView(APIView):
    """
    GET /api/search-doormen/?q=<search_term>
    Search for users by email or name who can be assigned as doormen.
    Returns users who have accounts but are not the current promoter.
    
    Promoter-only endpoint.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from django.contrib.auth.models import User as DjangoUser

        if not hasattr(request.user, 'promoter'):
            return Response({'error': 'Only promoters can search for doormen.'},
                            status=status.HTTP_403_FORBIDDEN)

        search_term = request.query_params.get('q', '').strip()
        if len(search_term) < 3:
            return Response({'error': 'Search term must be at least 3 characters.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Search users by email or name, exclude the current user
        users = DjangoUser.objects.filter(
            Q(email__icontains=search_term) |
            Q(first_name__icontains=search_term) |
            Q(last_name__icontains=search_term) |
            Q(username__icontains=search_term)
        ).exclude(
            id=request.user.id
        )[:20]  # Limit to 20 results

        result = [{
            'id': u.id,
            'name': u.get_full_name() if u.get_full_name() else u.username,
            'email': u.email or u.username
        } for u in users]

        return Response(result)


