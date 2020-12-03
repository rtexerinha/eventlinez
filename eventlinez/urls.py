from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

import shop
from shop.views import index
from event.views import order_promoter, events_promoter, new_events, order_per_events, remove_event
from customer.views import signup_view_promoter, signin_view_promoter, \
    signout_view_promoter

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    path('shop/', include('shop.urls')),
    path('about/', shop.views.about, name='about'),
    path('contact/', shop.views.contact, name='contact'),
    path('customer/', include('customer.urls')),
    path('promoter/account/create/', signup_view_promoter, name='signup_promoter'),
    path('promoter/account/login/', signin_view_promoter, name='signin_promoter'),
    path('promoter/account/logout/', signout_view_promoter, name='signout_promoter'),
    path('promoter/', order_promoter, name='order_promoter'),
    path('promoter/orders/', order_per_events, name='order_per_events'),
    path('promoter/events/', events_promoter, name='events_promoter'),
    path('promoter/events/new/', new_events, name='new_events'),
    path('promoter/events/full_remove/<int:event_id>/', remove_event, name='remove_event'),
]


admin.site.site_header = 'Eventlinez'
admin.site.index_title = 'Admin Panel'
admin.site.site_title = 'Welcome Eventlinez'
handler404 = shop.views.handler404

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
