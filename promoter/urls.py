from django.urls import path
from promoter.views import update_promoter, reset_password, signup_view_promoter, signin_view_promoter, \
    signout_view_promoter, vendors_list, vendor_create, vendor_update, vendor_remove, vendor_create_per_event, \
    vendor_update_per_event, vendors_reports, vendor_export_excel, payout_account_link, \
    balance_history_payout, payout_pdf_view, webhook_payout
from event.views import ticket_type_create, ticket_type_list, ticket_type_update, ticket_type_list_per_event
from ticket.views import tickets_sold_list, tickets_excel, ticket_checkin, tickets_validate
from event.views import event_list, event_create, event_remove, event_update

urlpatterns = [
    path('account/create/', signup_view_promoter, name='signup_promoter'),
    path('account/login/', signin_view_promoter, name='signin_promoter'),
    path('account/logout/', signout_view_promoter, name='signout_promoter'),
    path('update/', update_promoter, name='update_promoter'),
    path('reset_password/', reset_password, name='reset_password'),

    # Type Ticket
    path('ticket/new/<int:event_id>/', ticket_type_create, name='ticket_create'),
    path('ticket/update/<int:ticket_id>/', ticket_type_update, name='ticket_update'),
    path('ticket/type/list/<int:ticket_id>/', ticket_type_list, name='ticket_type_list'),
    path('ticket/type/list/', ticket_type_list, name='ticket_type_list'),
    path('ticket/type/event/<int:event_id>/', ticket_type_list_per_event, name='ticket_type_list_per_event'),

    # Ticket sold in panel promoter
    path('ticket/', tickets_sold_list, name='ticket_list'),
    path('ticket/<int:event_id>/', tickets_sold_list, name='ticket_list'),
    path('ticket/excel/<int:event_id>/', tickets_excel, name='tickets_excel'),
    path('ticket/excel/', tickets_excel, name='tickets_excel'),
    path('ticket/checkin/<uuid:checkin>/', ticket_checkin, name='ticket_checkin'),
    path('ticket/checkin/validate/', tickets_validate, name='tickets_validate'),

    # events
    path('events/new/', event_create, name='new_events'),
    path('events/', event_list, name='events_promoter'),
    path('events/update/<int:event_id>/', event_update, name='update_event'),
    path('events/full_remove/<int:event_id>/', event_remove, name='remove_event'),

    # Vendors
    path('vendors/report/list/', vendors_reports, name='vendors_reports'),
    path('vendors/', vendors_list, name='vendors_list'),
    path('vendor/new/', vendor_create, name='vendor_create'),
    path('vendor/new/<int:event_id>/', vendor_create_per_event, name='vendor_create_per_event'),
    path('vendor/update/event/<int:event_id>/', vendor_update_per_event, name='vendor_update_per_event'),
    path('vendor/update/<int:vendor_id>/', vendor_update, name='vendor_update'),
    path('vendor/remove/<int:vendor_id>/', vendor_remove, name='vendor_remove'),
    path('vendors/report/list/excel/<int:event_id>/', vendor_export_excel, name='vendor_export_excel'),

    # payout
    path('payout/', payout_account_link, name='payout_stripe'),
    path('payout/list/', balance_history_payout, name='balancehistorypayout'),
    path('payout/pdf/', payout_pdf_view, name='payout_pdf_view'),
    path('payout/webhook/', webhook_payout, name='webhook_payout'),
]
