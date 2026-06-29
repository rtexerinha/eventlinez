"""
Eventlinez Mobile API — all endpoints for the React Native app.

Auth header required for protected endpoints:
    Authorization: Token <token>
"""
import logging
from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from event.models import Category, Event, Ticket as EventTicket
from order.models import Order
from ticket.models import Ticket
from .models import TicketShareToken
from .serializers import (
    CartSerializer, CategorySerializer, ChangePasswordSerializer,
    EventDetailSerializer, EventListSerializer, LoginSerializer,
    OrderSerializer, PublicTicketSerializer, RegisterSerializer,
    TicketSerializer, TicketShareTokenSerializer, UserProfileSerializer,
)

logger = logging.getLogger(__name__)


# ─── helpers ─────────────────────────────────────────────────────────────────

def _get_or_create_api_cart(customer):
    """Stable cart per customer for the mobile API (no session needed)."""
    cart_id = f"api_customer_{customer.id}"
    cart, _ = Cart.objects.get_or_create(cart_id=cart_id)
    return cart


# ─── Phase 1 — Auth ──────────────────────────────────────────────────────────

class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email'].lower()
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)
        if not user:
            try:
                db_user = User.objects.get(username__iexact=email)
                user = authenticate(request, username=db_user.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        token, _ = Token.objects.get_or_create(user=user)
        is_promoter = hasattr(user, 'promoter')

        customer_data = {}
        if not is_promoter:
            try:
                c = user.customer
                customer_data = {
                    'id': c.id,
                    'first_name': c.first_name,
                    'last_name': c.last_name,
                    'email': c.email,
                    'cellphone': c.cellphone or '',
                }
            except Exception:
                pass

        return Response({
            'token': token.key,
            'is_promoter': is_promoter,
            'user': customer_data or {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
        })


class LogoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response({'detail': 'Logged out.'})


class MeView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)
        return Response(UserProfileSerializer(customer).data)

    def patch(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)
        serializer = UserProfileSerializer(customer, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response({'error': 'Current password is incorrect.'}, status=400)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        user.auth_token.delete()
        token = Token.objects.create(user=user)
        return Response({'token': token.key, 'detail': 'Password updated.'})


class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'error': 'Email is required.'}, status=400)
        try:
            user = User.objects.get(username__iexact=email)
            from django.contrib.auth.forms import PasswordResetForm
            form = PasswordResetForm({'email': user.email})
            if form.is_valid():
                form.save(
                    request=request,
                    use_https=request.is_secure(),
                    email_template_name='registration/password_reset_email.html',
                )
        except User.DoesNotExist:
            pass
        return Response({'detail': 'If an account exists, a reset email has been sent.'})


# ─── Phase 2 — Events ────────────────────────────────────────────────────────

class CategoryListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        cats = Category.objects.all().order_by('name')
        return Response(CategorySerializer(cats, many=True).data)


class EventListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db.models import Q
        qs = Event.objects.filter(available=True).select_related('category', 'city')

        q = request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(description__icontains=q))

        category = request.query_params.get('category', '').strip()
        if category:
            qs = qs.filter(category__slug=category)

        upcoming = request.query_params.get('upcoming', '').lower()
        if upcoming == 'true':
            qs = qs.filter(event_date__gte=timezone.now())
        elif upcoming == 'false':
            qs = qs.filter(event_date__lt=timezone.now())

        return Response(EventListSerializer(
            qs.order_by('-event_date'), many=True, context={'request': request}
        ).data)


class EventDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            event = Event.objects.select_related(
                'category', 'city', 'promoter'
            ).prefetch_related('tickets').get(slug=slug, available=True)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found.'}, status=404)
        return Response(EventDetailSerializer(event, context={'request': request}).data)


# ─── Phase 3 — Cart ──────────────────────────────────────────────────────────

class CartView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)
        cart = _get_or_create_api_cart(customer)
        if cart.is_expired():
            cart.clear_items()
        return Response(CartSerializer(cart).data)


class CartAddView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)

        ticket_id = request.data.get('ticket_id')
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid quantity.'}, status=400)

        if quantity < 1:
            return Response({'error': 'Quantity must be at least 1.'}, status=400)

        try:
            event_ticket = EventTicket.objects.select_related('event').get(id=ticket_id)
        except EventTicket.DoesNotExist:
            return Response({'error': 'Ticket type not found.'}, status=404)

        if event_ticket.sold_out:
            return Response({'error': 'This ticket type is sold out.'}, status=400)

        if event_ticket.sold_out or event_ticket.qty_available() < quantity:
            return Response({'error': 'Not enough tickets available.'}, status=400)
        if event_ticket.event.event_date < timezone.now():
            return Response({'error': 'This event has already passed.'}, status=400)

        cart = _get_or_create_api_cart(customer)
        if cart.is_expired():
            cart.clear_items()

        existing = cart.cartitem_set.filter(ticket=event_ticket, active=True).first()
        if existing:
            existing.quantity += quantity
            existing.save(update_fields=['quantity'])
        else:
            CartItem.objects.create(cart=cart, ticket=event_ticket, quantity=quantity, active=True, vendor=None)

        cart.reserved_at = timezone.now()
        cart.save(update_fields=['reserved_at'])
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)


class CartItemView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_item(self, request, item_id):
        try:
            customer = request.user.customer
        except Exception:
            return None, Response({'error': 'Customer profile not found.'}, status=404)
        cart = _get_or_create_api_cart(customer)
        try:
            return cart.cartitem_set.get(id=item_id, active=True), None
        except CartItem.DoesNotExist:
            return None, Response({'error': 'Item not found in cart.'}, status=404)

    def patch(self, request, item_id):
        item, err = self._get_item(request, item_id)
        if err:
            return err
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            return Response({'error': 'Invalid quantity.'}, status=400)
        if quantity < 1:
            return Response({'error': 'Quantity must be at least 1.'}, status=400)
        if item.ticket.qty_available() < quantity:
            return Response({'error': 'Not enough tickets available.'}, status=400)
        item.quantity = quantity
        item.save(update_fields=['quantity'])
        return Response(CartSerializer(item.cart).data)

    def delete(self, request, item_id):
        item, err = self._get_item(request, item_id)
        if err:
            return err
        cart = item.cart
        item.delete()
        if not cart.cartitem_set.filter(active=True).exists():
            cart.reserved_at = None
            cart.save(update_fields=['reserved_at'])
        return Response(CartSerializer(cart).data)


class CartPromoView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)

        code = request.data.get('code', '').strip().upper()
        if not code:
            return Response({'error': 'Promo code is required.'}, status=400)

        cart = _get_or_create_api_cart(customer)
        if not cart.cartitem_set.filter(active=True).exists():
            return Response({'error': 'Cart is empty.'}, status=400)

        try:
            from promoter.models import PromoCode
            first_item = cart.cartitem_set.filter(active=True).first()
            event = first_item.ticket.event if first_item else None
            promo = PromoCode.objects.get(code__iexact=code, event=event, is_active=True)

            now = timezone.now()
            if promo.valid_from and now < promo.valid_from:
                return Response({'error': 'Promo code is not active yet.'}, status=400)
            if promo.valid_until and now > promo.valid_until:
                return Response({'error': 'Promo code has expired.'}, status=400)
            if promo.max_uses and promo.current_uses >= promo.max_uses:
                return Response({'error': 'Promo code has reached its usage limit.'}, status=400)

            subtotal = cart.subtotal()
            if promo.discount_type == 'percentage':
                discount = (subtotal * Decimal(str(promo.discount_value))) / 100
            else:
                discount = Decimal(str(promo.discount_value))

            discount = min(discount, subtotal)
            cart.applied_promo_code = promo.code
            cart.promo_discount = discount
            cart.save(update_fields=['applied_promo_code', 'promo_discount'])

            return Response({
                'detail': f'Promo applied. Saving ${discount:.2f}.',
                'cart': CartSerializer(cart).data,
            })
        except Exception as exc:
            logger.warning(f"Promo code '{code}' error: {exc}")
            return Response({'error': 'Invalid or inapplicable promo code.'}, status=400)

    def delete(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)
        cart = _get_or_create_api_cart(customer)
        cart.applied_promo_code = None
        cart.promo_discount = Decimal('0.00')
        cart.save(update_fields=['applied_promo_code', 'promo_discount'])
        return Response(CartSerializer(cart).data)


class CartCheckoutView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)

        cart = _get_or_create_api_cart(customer)
        if cart.is_expired():
            cart.clear_items()
            return Response({'error': 'Cart reservation expired. Add tickets again.'}, status=400)

        items = cart.cartitem_set.filter(active=True)
        if not items.exists():
            return Response({'error': 'Cart is empty.'}, status=400)

        for item in items:
            if item.ticket.sold_out or item.ticket.qty_available() < item.quantity:
                return Response({'error': f'"{item.ticket.name}" is no longer available.'}, status=400)

        from django.conf import settings
        import stripe as _stripe
        _stripe.api_key = settings.STRIPE_SECRET_KEY
        total_amount = cart.total_with_promo()
        if total_amount <= 0:
            return Response({'error': 'Cart total cannot be zero.'}, status=400)

        try:
            from order.stripe_utils import build_stripe_description, build_stripe_metadata_from_cart
            first_item = items.first()
            description = build_stripe_description(
                first_item.ticket.event.name,
                first_item.ticket.name,
                customer_email=customer.email,
            )
            metadata = build_stripe_metadata_from_cart(cart, items, customer_email=customer.email)
            if cart.applied_promo_code:
                metadata['promo_code'] = cart.applied_promo_code
                metadata['promo_discount'] = str(cart.promo_discount)

            success_url = request.build_absolute_uri('/order/success/') + '?session_id={CHECKOUT_SESSION_ID}'
            cancel_url = request.build_absolute_uri('/')

            session = _stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'product_data': {
                            'name': f'Event Tickets ({items.count()} item{"s" if items.count() != 1 else ""})',
                        },
                        'unit_amount': int(total_amount * 100),
                        'currency': 'usd',
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                payment_intent_data={'description': description, 'metadata': metadata},
                client_reference_id=cart.id,
                customer_email=customer.email,
                allow_promotion_codes=False,
            )

            cart.reserved_at = timezone.now()
            cart.save(update_fields=['reserved_at'])

            return Response({'checkout_url': session.url, 'session_id': session.id})
        except Exception as exc:
            logger.error(f"API Stripe session creation failed: {exc}")
            return Response({'error': 'Payment session creation failed.'}, status=500)


# ─── Phase 4 — Orders ────────────────────────────────────────────────────────

class OrderListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)
        orders = Order.objects.filter(customer=customer).order_by('-id')
        return Response(OrderSerializer(orders, many=True, context={'request': request}).data)


class OrderDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)
        try:
            order = Order.objects.get(id=order_id, customer=customer)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found.'}, status=404)
        return Response(OrderSerializer(order, context={'request': request}).data)


# ─── Phase 5 — Tickets (wallet) ──────────────────────────────────────────────

class TicketListView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)

        tickets = list(Ticket.objects.filter(customer=customer).select_related(
            'event_ticket', 'event_ticket__event', 'day_event',
        ).order_by('-created_at'))

        now = timezone.now()
        filter_by = request.query_params.get('filter', 'all')
        if filter_by == 'upcoming':
            tickets = [t for t in tickets if (t.day_event or t.event_ticket.event).event_date >= now]
        elif filter_by == 'past':
            tickets = [t for t in tickets if (t.day_event or t.event_ticket.event).event_date < now]

        return Response(TicketSerializer(tickets, many=True, context={'request': request}).data)


class TicketDetailView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_ticket(self, request, ticket_id):
        try:
            customer = request.user.customer
        except Exception:
            return None, Response({'error': 'Customer profile not found.'}, status=404)
        try:
            return Ticket.objects.select_related(
                'event_ticket', 'event_ticket__event', 'day_event',
            ).get(id=ticket_id, customer=customer), None
        except Ticket.DoesNotExist:
            return None, Response({'error': 'Ticket not found.'}, status=404)

    def get(self, request, ticket_id):
        ticket, err = self._get_ticket(request, ticket_id)
        if err:
            return err
        return Response(TicketSerializer(ticket, context={'request': request}).data)

    def patch(self, request, ticket_id):
        ticket, err = self._get_ticket(request, ticket_id)
        if err:
            return err
        guest_name = request.data.get('guest_name', '').strip() or None
        ticket.guest_name = guest_name
        ticket.save(update_fields=['guest_name'])
        return Response(TicketSerializer(ticket, context={'request': request}).data)


class TicketQRView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, ticket_id):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)
        try:
            ticket = Ticket.objects.get(id=ticket_id, customer=customer)
        except Ticket.DoesNotExist:
            return Response({'error': 'Ticket not found.'}, status=404)
        try:
            svg = str(ticket.as_qrcode())
        except Exception as exc:
            logger.error(f"QR generation failed for ticket {ticket_id}: {exc}")
            return Response({'error': 'QR generation failed.'}, status=500)
        return Response({
            'ticket_id': ticket.id,
            'uuid': str(ticket.uuid),
            'qr_svg': svg,
        })


class TicketPDFView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, ticket_id):
        try:
            customer = request.user.customer
        except Exception:
            return Response({'error': 'Customer profile not found.'}, status=404)
        try:
            ticket = Ticket.objects.get(id=ticket_id, customer=customer)
        except Ticket.DoesNotExist:
            return Response({'error': 'Ticket not found.'}, status=404)
        try:
            pdf = ticket.as_pdf()
        except Exception as exc:
            logger.error(f"PDF generation failed for ticket {ticket_id}: {exc}")
            return Response({'error': 'PDF generation failed.'}, status=500)
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ticket_{ticket.id}.pdf"'
        return response


# ─── Phase 7 — Ticket sharing ────────────────────────────────────────────────

class TicketShareView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _get_ticket(self, request, ticket_id):
        try:
            customer = request.user.customer
        except Exception:
            return None, Response({'error': 'Customer profile not found.'}, status=404)
        try:
            return Ticket.objects.get(id=ticket_id, customer=customer), None
        except Ticket.DoesNotExist:
            return None, Response({'error': 'Ticket not found.'}, status=404)

    def get(self, request, ticket_id):
        ticket, err = self._get_ticket(request, ticket_id)
        if err:
            return err
        tokens = ticket.share_tokens.filter(revoked=False, expires_at__gt=timezone.now())
        return Response(TicketShareTokenSerializer(tokens, many=True, context={'request': request}).data)

    def post(self, request, ticket_id):
        ticket, err = self._get_ticket(request, ticket_id)
        if err:
            return err
        token = TicketShareToken.objects.create(ticket=ticket)
        return Response(
            TicketShareTokenSerializer(token, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, ticket_id):
        ticket, err = self._get_ticket(request, ticket_id)
        if err:
            return err
        ticket.share_tokens.filter(revoked=False).update(revoked=True)
        return Response({'detail': 'All share tokens revoked.'})


class PublicTicketView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def _resolve(self, token_str):
        import uuid as _uuid
        try:
            token_uuid = _uuid.UUID(str(token_str))
            share = TicketShareToken.objects.select_related(
                'ticket', 'ticket__event_ticket', 'ticket__event_ticket__event', 'ticket__day_event',
            ).get(token=token_uuid)
        except (TicketShareToken.DoesNotExist, ValueError):
            return None, Response({'error': 'Invalid or expired share link.'}, status=404)
        if not share.is_valid:
            return None, Response({'error': 'This share link has expired or been revoked.'}, status=410)
        return share.ticket, None

    def get(self, request, token):
        ticket, err = self._resolve(token)
        if err:
            return err
        return Response(PublicTicketSerializer(ticket, context={'request': request}).data)


class PublicTicketQRView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, token):
        import uuid as _uuid
        try:
            token_uuid = _uuid.UUID(str(token))
            share = TicketShareToken.objects.select_related('ticket').get(token=token_uuid)
        except (TicketShareToken.DoesNotExist, ValueError):
            return Response({'error': 'Invalid or expired share link.'}, status=404)
        if not share.is_valid:
            return Response({'error': 'This share link has expired or been revoked.'}, status=410)
        try:
            svg = str(share.ticket.as_qrcode())
        except Exception as exc:
            logger.error(f"QR generation failed for share token {token}: {exc}")
            return Response({'error': 'QR generation failed.'}, status=500)
        return Response({'uuid': str(share.ticket.uuid), 'qr_svg': svg, 'expires_at': share.expires_at})
