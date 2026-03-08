from django.urls import path
from promoter.views import update_promoter, reset_password, signup_view_promoter, signin_view_promoter, \
    signout_view_promoter, vendors_list, vendor_create, vendor_update, vendor_remove, vendor_create_per_event, \
    vendor_update_per_event, vendors_reports, vendor_export_excel, \
    payment_list, payment_pdf_view, bank_account_list, bank_create, \
    bank_account_update, bank_remove, promo_codes_list, promo_code_create, \
    promo_code_update, promo_code_delete, promo_code_toggle_status, promoter_dashboard, \
    revenue_report, revenue_report_export, guest_lists_overview, doorman_dashboard, doorman_checkin_page, \
    partners_list, partner_create, doorman_create, partner_toggle_status, partner_delete
from event.views import ticket_type_create, ticket_type_list, ticket_type_update, ticket_type_list_per_event
from ticket.views import tickets_sold_list, tickets_excel, ticket_checkin, tickets_validate
from ticket.views_complimentary import (
    guest_list, create_complimentary_ticket, bulk_create_complimentary_tickets,
    view_complimentary_ticket, download_complimentary_ticket_pdf,
    send_complimentary_ticket_email_view, cancel_complimentary_ticket,
    complimentary_ticket_checkin, download_complimentary_ticket_qr,
    get_whatsapp_share_link, get_sms_link, share_ticket_options
)
from event.views import event_list, event_create, event_remove, event_update
from .api import CustomAuthToken, PromoterListAPIView, EventListAPIView, CategoryListAPIView, TicketTypeAPIView, \
    EventUpdateAPIView, TicketTypeUpdateAPIView, EventDetailsAPIView, sales_report, TicketTypeListView, \
    EventCreateAPIView, PartnerCreateAPIView, PartnerUpdateAPIView, PartnerListView, \
    EventCreateAPIView, TicketSoldOutUpdateAPIView, PromoCodeListCreateAPIView, PromoCodeDetailAPIView, \
    PromoCodeToggleAPIView, PromoCodeValidateAPIView, GuestListAPIView, GuestBulkCreateAPIView, GuestDetailAPIView, \
    GuestResendEmailAPIView, GuestShareLinksAPIView, GuestCheckinAPIView, \
    DoormanProfileAPIView, DoormanEventListAPIView, DoormanCheckinStatsAPIView, \
    DoormanScanPaidTicketAPIView, DoormanScanGuestTicketAPIView, \
    DoormanAssignAPIView, DoormanListAPIView, \
    EventDoormenAPIView, AvailableDoormenAPIView, SearchUsersForDoormanAPIView

app_name = 'promoter'

urlpatterns = [
    # Dashboard - Main promoter landing page
    path('dashboard/', promoter_dashboard, name='promoter_dashboard'),
    
    # Doorman Web Interface
    path('doorman/', doorman_dashboard, name='doorman_dashboard'),
    path('doorman/event/<int:event_id>/checkin/', doorman_checkin_page, name='doorman_checkin_page'),
    
    # Partners Management
    path('partners/', partners_list, name='partners_list'),
    path('partners/create/', partner_create, name='partner_create'),
    path('partners/doorman/create/', doorman_create, name='doorman_create'),
    path('partners/<int:partner_id>/toggle/', partner_toggle_status, name='partner_toggle_status'),
    path('partners/<int:partner_id>/delete/', partner_delete, name='partner_delete'),
    
    # Account management
    path('account/create/', signup_view_promoter, name='signup_promoter'),
    path('account/login/', signin_view_promoter, name='signin_promoter'),
    path('account/logout/', signout_view_promoter, name='signout_promoter'),
    path('update/', update_promoter, name='update_promoter'),
    path('reset_password/', reset_password, name='reset_password'),

    # Type Ticket
    path('ticket/new/<int:event_id>/', ticket_type_create, name='ticket_create'),
    path('ticket/update/<int:ticket_id>/',
         ticket_type_update, name='ticket_update'),
    path('ticket/type/list/<int:ticket_id>/',
         ticket_type_list, name='ticket_type_list'),
    path('ticket/type/list/', ticket_type_list, name='ticket_type_list'),
    path('ticket/type/event/<int:event_id>/',
         ticket_type_list_per_event, name='ticket_type_list_per_event'),

    # Ticket sold in panel promoter
    path('ticket/', tickets_sold_list, name='ticket_list'),
    path('ticket/<int:event_id>/', tickets_sold_list, name='ticket_list'),
    path('ticket/excel/<int:event_id>/', tickets_excel, name='tickets_excel'),
    path('ticket/excel/', tickets_excel, name='tickets_excel'),
    path('ticket/checkin/<uuid:checkin>/',
         ticket_checkin, name='ticket_checkin'),
    path('ticket/checkin/validate/', tickets_validate, name='tickets_validate'),
    
    # Guest Lists Overview
    path('guest-lists/', guest_lists_overview, name='guest_lists_overview'),
    
    # Complimentary Tickets / Guest List
    path('event/<int:event_id>/guest-list/', guest_list, name='guest_list'),
    path('event/<int:event_id>/guest-list/create/', create_complimentary_ticket, name='create_complimentary_ticket'),
    path('event/<int:event_id>/guest-list/bulk/', bulk_create_complimentary_tickets, name='bulk_create_complimentary_tickets'),
    path('complimentary-ticket/<int:ticket_id>/', view_complimentary_ticket, name='view_complimentary_ticket'),
    path('complimentary-ticket/<int:ticket_id>/pdf/', download_complimentary_ticket_pdf, name='download_complimentary_ticket_pdf'),
    path('complimentary-ticket/<int:ticket_id>/qr/', download_complimentary_ticket_qr, name='download_complimentary_ticket_qr'),
    path('complimentary-ticket/<int:ticket_id>/send/', send_complimentary_ticket_email_view, name='send_complimentary_ticket'),
    path('complimentary-ticket/<int:ticket_id>/whatsapp/', get_whatsapp_share_link, name='get_whatsapp_share_link'),
    path('complimentary-ticket/<int:ticket_id>/sms/', get_sms_link, name='get_sms_link'),
    path('complimentary-ticket/<int:ticket_id>/share/', share_ticket_options, name='share_ticket_options'),
    path('complimentary-ticket/<int:ticket_id>/cancel/', cancel_complimentary_ticket, name='cancel_complimentary_ticket'),
    path('ticket/complimentary/checkin/<uuid:uuid>/', complimentary_ticket_checkin, name='complimentary_ticket_checkin'),

    # events
    path('events/new/', event_create, name='new_events'),
    path('events/', event_list, name='events_promoter'),
    path('events/update/<int:event_id>/', event_update, name='update_event'),
    path('events/full_remove/<int:event_id>/',
         event_remove, name='remove_event'),

    # Vendors
    path('vendors/report/list/', vendors_reports, name='vendors_reports'),
    path('vendors/', vendors_list, name='vendors_list'),
    path('vendor/new/', vendor_create, name='vendor_create'),
    path('vendor/new/<int:event_id>/', vendor_create_per_event,
         name='vendor_create_per_event'),
    path('vendor/update/event/<int:event_id>/',
         vendor_update_per_event, name='vendor_update_per_event'),
    path('vendor/update/<int:vendor_id>/', vendor_update, name='vendor_update'),
    path('vendor/remove/<int:vendor_id>/', vendor_remove, name='vendor_remove'),
    path('vendors/report/list/excel/<int:event_id>/',
         vendor_export_excel, name='vendor_export_excel'),

    # Payments
    path('payment/list/', payment_list, name='payment_list'),
    path('payment/pdf/', payment_pdf_view, name='payout_pdf_view'),

    # bank
    path('bank/create/', bank_create, name='bank_create'),
    path('bank/information/', bank_account_list, name='bank_information'),
    path('bank/update/<int:bank_id>/',
         bank_account_update, name='bank_account_update'),
    path('bank/remove/<int:bank_id>/', bank_remove, name='bank_remove'),

    # Promo Codes
    path('promo-codes/', promo_codes_list, name='promo_codes_list'),
    path('promo-codes/new/', promo_code_create, name='promo_code_create'),
    path('promo-codes/<int:promo_code_id>/edit/', promo_code_update, name='promo_code_update'),
    path('promo-codes/<int:promo_code_id>/delete/', promo_code_delete, name='promo_code_delete'),
    path('promo-codes/<int:promo_code_id>/toggle/', promo_code_toggle_status, name='promo_code_toggle_status'),

    # Reports
    path('reports/revenue/', revenue_report, name='revenue_report'),
    path('reports/revenue/export/<int:event_id>/', revenue_report_export, name='revenue_report_export'),

    # auth
    path('api-token-auth/', CustomAuthToken.as_view()),
    path('api/information/', PromoterListAPIView.as_view()),

    # API events
    path('api/event', EventListAPIView.as_view()),
    path('api/event/create', EventCreateAPIView.as_view()),
    path('api/event/update/<int:pk>', EventUpdateAPIView.as_view()),
    path('api/event/<int:pk>', EventDetailsAPIView.as_view()), # Event details mobile
    path("api/event/<int:event_id>/salesReport", sales_report),

    path('api/categories', CategoryListAPIView.as_view()),

    # APIs ticketType
    path('api/ticket/type', TicketTypeAPIView.as_view()),
    path('api/ticket/type/update/<int:pk>', TicketTypeUpdateAPIView.as_view()),
    path('api/event/<int:event_id>/tickets/type', TicketTypeListView.as_view()),


    # APIs partner or doorman
    path('api/partner', PartnerCreateAPIView.as_view()),
    path('api/partner/update/<int:pk>', PartnerUpdateAPIView.as_view()),
    path('api/event/<int:event_id>/partner', PartnerListView.as_view()),
    
    path('api/ticket/<int:pk>/sold-out/', TicketSoldOutUpdateAPIView.as_view(), name="ticket_sold_out"),

    # ── Promo Code API ────────────────────────────────────────────────────────
    # Promoter: list all / create
    path('api/promo-codes/', PromoCodeListCreateAPIView.as_view(), name='api_promo_codes'),
    # Public: validate a code (no auth needed)
    path('api/promo-codes/validate/', PromoCodeValidateAPIView.as_view(), name='api_promo_code_validate'),
    # Promoter: retrieve / partial-update / delete a specific code
    path('api/promo-codes/<int:pk>/', PromoCodeDetailAPIView.as_view(), name='api_promo_code_detail'),
    # Promoter: toggle active/inactive
    path('api/promo-codes/<int:pk>/toggle/', PromoCodeToggleAPIView.as_view(), name='api_promo_code_toggle'),

    # ── Guest List API ────────────────────────────────────────────────────────
    # Promoter: list guests / add single guest
    path('api/guest-list/', GuestListAPIView.as_view(), name='api_guest_list'),
    # Promoter: bulk add guests
    path('api/guest-list/bulk/', GuestBulkCreateAPIView.as_view(), name='api_guest_list_bulk'),
    # Public (QR scan): check-in by UUID
    path('api/guest-list/checkin/<uuid:uuid>/', GuestCheckinAPIView.as_view(), name='api_guest_checkin'),
    # Promoter: retrieve / update / cancel a single guest ticket
    path('api/guest-list/<int:pk>/', GuestDetailAPIView.as_view(), name='api_guest_detail'),
    # Promoter: resend ticket email
    path('api/guest-list/<int:pk>/resend/', GuestResendEmailAPIView.as_view(), name='api_guest_resend'),
    # Promoter: get WhatsApp / SMS / QR share links
    path('api/guest-list/<int:pk>/share/', GuestShareLinksAPIView.as_view(), name='api_guest_share'),

    # ── Doorman API ───────────────────────────────────────────────────────────
    # Doorman: their own profile + assigned events with live counters
    path('api/doorman/profile/', DoormanProfileAPIView.as_view(), name='api_doorman_profile'),
    # Doorman: list assigned events (?state=current|all)
    path('api/doorman/events/', DoormanEventListAPIView.as_view(), name='api_doorman_events'),
    # Doorman: live stats for a specific event
    path('api/doorman/events/<int:event_id>/stats/', DoormanCheckinStatsAPIView.as_view(), name='api_doorman_stats'),
    # Doorman: scan a paid ticket QR code
    path('api/doorman/scan/ticket/', DoormanScanPaidTicketAPIView.as_view(), name='api_doorman_scan_ticket'),
    # Doorman: scan a guest-list (complimentary) ticket QR code
    path('api/doorman/scan/guest/', DoormanScanGuestTicketAPIView.as_view(), name='api_doorman_scan_guest'),
    # Promoter: assign a doorman to an event
    path('api/doorman/assign/', DoormanAssignAPIView.as_view(), name='api_doorman_assign'),
    # Promoter: disable/remove a doorman assignment
    path('api/doorman/assign/<int:partner_id>/', DoormanAssignAPIView.as_view(), name='api_doorman_assign_remove'),
    # Promoter: list all doormen (?event_id=<id>)
    path('api/doorman/list/', DoormanListAPIView.as_view(), name='api_doorman_list'),
    
    # ── Event Doormen API (for mobile app) ────────────────────────────────────
    # Get all doormen assigned to a specific event
    path('api/event-doormen/', EventDoormenAPIView.as_view(), name='api_event_doormen'),
    # Get available doormen (previously used) that can be assigned to an event
    path('api/available-doormen/', AvailableDoormenAPIView.as_view(), name='api_available_doormen'),
    # Search for users to assign as doormen
    path('api/search-doormen/', SearchUsersForDoormanAPIView.as_view(), name='api_search_doormen'),
]
