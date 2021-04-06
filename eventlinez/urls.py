from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views


import shop
from shop.views import index
from event.views import event_list, event_create, event_remove, event_update, tickets_list, tickets_excel, update_promoter, reset_password
from customer.views import signup_view_promoter, signin_view_promoter, signout_view_promoter, signin_view

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
    path('promoter/update/', update_promoter, name='update_promoter'),
    path('promoter/reset_password', reset_password, name='reset_password'),




    path('promoter/ticket/', tickets_list, name='ticket_list'),
    path('promoter/ticket/<int:event_id>/', tickets_list, name='ticket_list'),
    path('promoter/ticket/excel/', tickets_excel, name='tickets_excel'),
    # path('promoter/ticket/excel/<int:event_id>/', tickets_excel, name='tickets_excel'),

    # CRUD events
    path('promoter/events/new/', event_create, name='new_events'),
    path('promoter/events/', event_list, name='events_promoter'),
    path('promoter/events/update/<int:event_id>/', event_update, name='update_event'),
    path('promoter/events/full_remove/<int:event_id>/', event_remove, name='remove_event'),

    #recover password
    path('reset_password/', auth_views.PasswordResetView.as_view(), name="password_reset"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

]


admin.site.site_header = 'Eventlinez'
admin.site.index_title = 'Admin Panel'
admin.site.site_title = 'Welcome Eventlinez'
handler404 = shop.views.handler404

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
