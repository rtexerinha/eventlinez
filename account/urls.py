from django.urls import path
from .api import UserDetailAPI
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

_RESET_CTX = {'domain': 'www.eventlinez.com', 'site_name': 'Eventlinez', 'protocol': 'https'}

urlpatterns = [
    path('profile', UserDetailAPI.as_view(), name='userdetail'),

    # Reset password views customer
    path('reset_password/', auth_views.PasswordResetView.as_view(
        html_email_template_name='registration/password_reset_email.html',
        extra_email_context=_RESET_CTX,
    ), name="password_reset"),
    path('reset_password_sent/',
         auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path('reset/<uidb64>/<token>',
         auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('reset_password_complete/',
         auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path('reset_password/promoter',
         auth_views.PasswordResetView.as_view(
             html_email_template_name='registration/password_reset_email_promoter.html',
             extra_email_context=_RESET_CTX,
             success_url=reverse_lazy('password_reset_done_promoter')),
         name="password_reset_promoter"),

    path('reset_password_sent/promoter',
         auth_views.PasswordResetDoneView.as_view(), name="password_reset_done_promoter"),

    path('reset/promoter/<uidb64>/<token>',
         auth_views.PasswordResetConfirmView.as_view(
             success_url=reverse_lazy('password_reset_complete_promoter')),
         name="password_reset_confirm_promoter"),

    path('reset_password_complete/promoter',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete_promoter.html'),
         name="password_reset_complete_promoter"),
]
