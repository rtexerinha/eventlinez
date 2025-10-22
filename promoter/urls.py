from django.urls import path
from promoter.views import update_promoter, reset_password, signup_view_promoter, signin_view_promoter, \
    signout_view_promoter, vendors_list, vendor_create, vendor_update, vendor_remove, vendor_create_per_event, \
    vendor_update_per_event, vendors_reports, vendor_export_excel, \
    payment_list, payment_pdf_view, bank_account_list, bank_create, \
    bank_account_update, bank_remove, promo_codes_list, promo_code_create, \
    promo_code_update, promo_code_delete, promo_code_toggle_status, promoter_dashboard
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
    EventCreateAPIView, TicketSoldOutUpdateAPIView

app_name = 'promoter'

urlpatterns = [
    # Dashboard - Main promoter landing page
    path('dashboard/', promoter_dashboard, name='promoter_dashboard'),
    
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


]
