from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # ── Phase 1: Auth ────────────────────────────────────────────────────────
    path('auth/register/',          views.RegisterView.as_view(),           name='register'),
    path('auth/login/',             views.LoginView.as_view(),              name='login'),
    path('auth/logout/',            views.LogoutView.as_view(),             name='logout'),
    path('auth/me/',                views.MeView.as_view(),                 name='me'),
    path('auth/password/change/',   views.ChangePasswordView.as_view(),     name='change_password'),
    path('auth/password/reset/',    views.PasswordResetRequestView.as_view(), name='password_reset'),

    # ── Phase 2: Events ──────────────────────────────────────────────────────
    path('categories/',             views.CategoryListView.as_view(),       name='categories'),
    path('events/',                 views.EventListView.as_view(),          name='event_list'),
    path('events/<slug:slug>/',     views.EventDetailView.as_view(),        name='event_detail'),

    # ── Phase 3: Cart ────────────────────────────────────────────────────────
    path('cart/',                   views.CartView.as_view(),               name='cart'),
    path('cart/add/',               views.CartAddView.as_view(),            name='cart_add'),
    path('cart/items/<int:item_id>/', views.CartItemView.as_view(),         name='cart_item'),
    path('cart/promo/',             views.CartPromoView.as_view(),          name='cart_promo'),
    path('cart/checkout/',          views.CartCheckoutView.as_view(),       name='cart_checkout'),

    # ── Phase 4: Orders ──────────────────────────────────────────────────────
    path('orders/',                 views.OrderListView.as_view(),          name='order_list'),
    path('orders/<int:order_id>/',  views.OrderDetailView.as_view(),        name='order_detail'),

    # ── Phase 5: Tickets (wallet) ────────────────────────────────────────────
    path('tickets/',                        views.TicketListView.as_view(),     name='ticket_list'),
    path('tickets/<int:ticket_id>/',        views.TicketDetailView.as_view(),   name='ticket_detail'),
    path('tickets/<int:ticket_id>/qr/',     views.TicketQRView.as_view(),       name='ticket_qr'),
    path('tickets/<int:ticket_id>/pdf/',    views.TicketPDFView.as_view(),      name='ticket_pdf'),

    # ── Phase 7: Ticket sharing ──────────────────────────────────────────────
    path('tickets/<int:ticket_id>/share/',  views.TicketShareView.as_view(),    name='ticket_share'),
    path('t/<uuid:token>/',                 views.PublicTicketView.as_view(),   name='public_ticket'),
    path('t/<uuid:token>/qr/',              views.PublicTicketQRView.as_view(), name='public_ticket_qr'),
]
