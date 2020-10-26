from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.index, name='index'),
    path('<slug:c_slug>/', views.index, name='events_by_category'),
    path('<slug:c_slug>/<slug:event_slug>/', views.product_event_detail, name='product_event_detail'),
]
