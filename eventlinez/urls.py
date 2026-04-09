from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.views.static import serve
import os

import shop
from shop.views import index
from customer.views import signin_view
from shop.sitemaps import EventSitemap, StaticSitemap, HomeSitemap
from promoter.views_admin import (
    payout_report, payout_report_events_ajax,
    payout_report_export, payout_report_send_email,
)

sitemaps = {
    'home':   HomeSitemap,
    'events': EventSitemap,
    'static': StaticSitemap,
}

urlpatterns = []

# Add media files for development and Docker environment first
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif os.path.exists('/.dockerenv') or os.environ.get('IN_DOCKER', False):
    # For Docker environment, manually add media serving
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]

urlpatterns += [
    path('admin/', admin.site.urls),
    # Payout report — admin-only (staff_member_required inside the view)
    path('admin/payout-report/', payout_report, name='admin_payout_report'),
    path('admin/payout-report/events/', payout_report_events_ajax, name='admin_payout_events_ajax'),
    path('admin/payout-report/export/<int:event_id>/', payout_report_export, name='admin_payout_export'),
    path('admin/payout-report/email/<int:event_id>/', payout_report_send_email, name='admin_payout_send_email'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', shop.views.robots_txt, name='robots_txt'),
    path('', index, name='index'),
    path('accounts/login/', signin_view, name='signin'),
    path('customer/', include('customer.urls')),
    path('promoter/', include('promoter.urls', namespace='promoter')),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    path('shop/', include('shop.urls')),
    path('ticket/', include('ticket.urls')),
    path('about/', shop.views.about, name='about'),
    path('contact/', shop.views.contact, name='contact'),
    path('terms-of-service/', shop.views.terms, name='terms'),
    path('account/',  include('account.urls'), name='account'),
    path('address/', include('address.urls'))
]

admin.site.site_header = 'Eventlinez'
admin.site.index_title = 'Admin Panel'
admin.site.site_title = 'Welcome Eventlinez'
handler404 = shop.views.handler404
handler500 = shop.views.handler500
