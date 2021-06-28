from django.urls import path
from event.views import update_promoter, reset_password
from customer.views import signup_view_promoter, signin_view_promoter, signout_view_promoter
from event.views import ticket_type_create, ticket_type_list, ticket_type_update, ticket_type_list_per_event
from ticket.views import tickets_sold_list, tickets_excel
from event.views import event_list, event_create, event_remove, event_update

urlpatterns = [
    path('account/create/', signup_view_promoter, name='signup_promoter'),
    path('account/login/', signin_view_promoter, name='signin_promoter'),
    path('account/logout/', signout_view_promoter, name='signout_promoter'),
    path('update/', update_promoter, name='update_promoter'),
    path('reset_password/', reset_password, name='reset_password'),

    # Type Ticket
    path('ticket/new/', ticket_type_create, name='ticket_create'),
    path('ticket/update/<int:ticket_id>/', ticket_type_update, name='ticket_update'),
    path('ticket/type/list/<int:ticket_id>/', ticket_type_list, name='ticket_type_list'),
    path('ticket/type/list/', ticket_type_list, name='ticket_type_list'),
    path('ticket/type/event/<int:event_id>/', ticket_type_list_per_event, name='ticket_type_list_per_event'),

    # Ticket sold in panel promoter
    path('ticket/', tickets_sold_list, name='ticket_list'),
    path('ticket/<int:event_id>/', tickets_sold_list, name='ticket_list'),
    path('ticket/excel/<int:event_id>/', tickets_excel, name='tickets_excel'),
    path('ticket/excel/', tickets_excel, name='tickets_excel'),

    # events
    path('events/new/', event_create, name='new_events'),
    path('events/', event_list, name='events_promoter'),
    path('events/update/<int:event_id>/', event_update, name='update_event'),
    path('events/full_remove/<int:event_id>/', event_remove, name='remove_event'),
]
