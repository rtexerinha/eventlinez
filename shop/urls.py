from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.all_event_categories, name='all_event_categories'),
    path('<slug:c_slug>/', views.all_event_categories, name='events_by_category'),
    path('<slug:c_slug>/<slug:event_slug>/', views.product_event_detail, name='product_event_detail'),
]
