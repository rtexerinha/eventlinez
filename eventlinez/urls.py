from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

import shop
from shop.views import index
from event.views import order_promoter, events_promoter, new_events, tickets_list_events, remove_event, \
    export_orders_csv, update_event, tickets_list, tickets_csv, tickets_excel
from customer.views import signup_view_promoter, signin_view_promoter, \
    signout_view_promoter, signin_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('accounts/login/', signin_view, name='signin'),

    # Urls de apps
    path('customer/', include('customer.urls')),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    path('shop/', include('shop.urls')),

    # Pages statics
    path('about/', shop.views.about, name='about'),
    path('contact/', shop.views.contact, name='contact'),

    # Promoter
    path('promoter/account/create/', signup_view_promoter, name='signup_promoter'),
    path('promoter/account/login/', signin_view_promoter, name='signin_promoter'),
    path('promoter/account/logout/', signout_view_promoter, name='signout_promoter'),
    path('promoter/', events_promoter, name='order_promoter'),
    path('promoter/export/', export_orders_csv, name='export_orders'),

    path('promoter/ticket/', tickets_list, name='ticket_list'),
    path('promoter/ticket/<int:event_id>/', tickets_list_events, name='ticket_list_events'),
    path('promoter/ticket/export/', tickets_csv, name='tickets_csv'),
    path('promoter/ticket/excel/', tickets_excel, name='tickets_excel'),

    # CRUD events
    path('promoter/events/new/', new_events, name='new_events'),
    path('promoter/events/', events_promoter, name='events_promoter'),
    path('promoter/events/update/<int:event_id>/', update_event, name='update_event'),
    path('promoter/events/full_remove/<int:event_id>/', remove_event, name='remove_event'),
]


admin.site.site_header = 'Eventlinez'
admin.site.index_title = 'Admin Panel'
admin.site.site_title = 'Welcome Eventlinez'
handler404 = shop.views.handler404

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
