from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
import os

import shop
from shop.views import index
from customer.views import signin_view
from shop.views import index

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
