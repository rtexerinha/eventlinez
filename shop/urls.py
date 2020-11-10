from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.index, name='index'),
    path('search', views.search_result, name='search'),
    path('<slug:c_slug>/', views.index, name='events_by_category'),
    path('add/<slug:event_slug>/', views.add_event, name='add_event'),
    path('<slug:c_slug>/<slug:event_slug>/', views.product_event_detail, name='product_event_detail'),
]
