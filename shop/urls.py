from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.index, name='index'),
    path('search', views.search_result, name='search'),
    path('<slug:c_slug>/', views.index, name='events_by_category'),
    path('<slug:c_slug>/<slug:event_slug>/', views.product_event_detail, name='product_event_detail'),
    
    # Gallery URLs
    path('gallery/', views.gallery_home, name='gallery_home'),
    path('gallery/<slug:event_slug>/', views.event_gallery, name='event_gallery'),
    path('gallery/download/<int:photo_id>/', views.download_photo, name='download_photo'),
]
