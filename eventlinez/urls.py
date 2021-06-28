from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

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
    path('about/', shop.views.about, name='about'),
    path('contact/', shop.views.contact, name='contact'),
    path('terms-of-service/', shop.views.terms, name='terms'),


    # Reset password views customer
    path('account/reset_password/', auth_views.PasswordResetView.as_view(
        html_email_template_name='registration/password_reset_email.html'), name="password_reset"),
    path('account/reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('account/reset/<uidb64>/<token>',
         auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('account/reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    # Reset password views promoter
    path('account/reset_password/promoter',
         auth_views.PasswordResetView.as_view(
             html_email_template_name='registration/password_reset_email_promoter.html',
             success_url=reverse_lazy('password_reset_done_promoter')),
         name="password_reset_promoter"),

    path('account/reset_password_sent/promoter',
         auth_views.PasswordResetDoneView.as_view(), name="password_reset_done_promoter"),

    path('account/reset/promoter/<uidb64>/<token>',
         auth_views.PasswordResetConfirmView.as_view(success_url=reverse_lazy('password_reset_complete_promoter')),
         name="password_reset_confirm_promoter"),

    path('account/reset_password_complete/promoter',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete_promoter.html'),
         name="password_reset_complete_promoter"),
]

admin.site.site_header = 'Eventlinez'
admin.site.index_title = 'Admin Panel'
admin.site.site_title = 'Welcome Eventlinez'
handler404 = shop.views.handler404
handler500 = shop.views.handler500

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
