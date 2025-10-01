from django.urls import path
from . import views
from . import bulk_upload_view

app_name = 'shop'

urlpatterns = [
    # Bulk upload URLs (must be first to avoid slug conflicts)
    path('gallery-admin/bulk-upload/', bulk_upload_view.bulk_upload_view, name='bulk_upload'),
    path('gallery-admin/bulk-upload/handle/', bulk_upload_view.handle_bulk_upload, name='bulk_upload_handle'),
    
    # Gallery URLs
    path('gallery/', views.gallery_home, name='gallery_home'),
    path('gallery/<slug:event_slug>/photos.json', views.event_photos_json, name='event_photos_json'),
    path('gallery/<slug:event_slug>/', views.event_gallery, name='event_gallery'),
    path('gallery/download/<int:photo_id>/', views.download_photo, name='download_photo'),
    
    # Main shop URLs
    path('', views.index, name='index'),
    path('search', views.search_result, name='search'),
    path('<slug:c_slug>/', views.index, name='events_by_category'),
    path('<slug:c_slug>/<slug:event_slug>/', views.product_event_detail, name='product_event_detail'),
]
