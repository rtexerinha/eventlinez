from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include


import shop
from shop.views import index
from customer.views import signin_view
from shop.views import index

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('accounts/login/', signin_view, name='signin'),
    path('customer/', include('customer.urls')),
    path('promoter/', include('promoter.urls')),
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
from django.conf import settings
from django.conf.urls.static import static

# Properly serve media and static files
# For Docker development environment, serve static files even when DEBUG=False
import os
if settings.DEBUG or os.path.exists('/.dockerenv') or os.environ.get('IN_DOCKER', False):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    print(f"Static files serving enabled. DEBUG={settings.DEBUG}, Docker={os.path.exists('/.dockerenv')}")
else:
    # In production, you should use a proper web server to serve static files
    # This is a fallback to handle media files in production for testing purposes
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    print("Static files serving disabled - using production setup")
