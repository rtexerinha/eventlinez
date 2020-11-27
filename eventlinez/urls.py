from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

import shop
from event.views import order_promoter, events_promoter
from customer.views import signout_view, signup_view, signin_view, signup_view_promoter, signin_view_promoter, \
    signout_view_promoter

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/promoter/', order_promoter, name='order_promoter'),
    path('admin/promoter/events', events_promoter, name='events_promoter'),
    path('shop/', include('shop.urls')),
    path('about/', shop.views.about, name='about'),
    path('contact/', shop.views.contact, name='contact'),
    path('', shop.views.index, name='index'),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    path('account/create/', signup_view, name='signup'),
    path('account/login/', signin_view, name='signin'),
    path('account/logout/', signout_view, name='signout'),
    path('account/promoter/creater/', signup_view_promoter, name='signup_promoter'),
    path('account/promoter/login/', signin_view_promoter, name='signin_promoter'),
    path('account/logout/promoter/', signout_view_promoter, name='signout_promoter'),
]


admin.site.site_header = 'Eventlinez'
admin.site.index_title = 'Admin Panel'
admin.site.site_title = 'Welcome Eventlinez'
handler404 = shop.views.handler404

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
