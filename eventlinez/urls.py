"""eventlinez URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

import shop
from shop import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('shop/', include('shop.urls')),
    path('about/', shop.views.about, name='about'),
    path('contact/', shop.views.contact, name='contact'),
    path('', views.index, name='index'),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),
    path('account/create/', views.signup_view, name='signup'),
    path('account/login/', views.signin_view, name='signin'),
    path('account/logout/', views.signout_view, name='signout'),
]


admin.site.site_header = 'Eventlinez'
admin.site.index_title = 'Admin Panel'
admin.site.site_title = 'Welcome Eventlinez'
handler404 = views.handler404

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
