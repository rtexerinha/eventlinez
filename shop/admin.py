from django.contrib import admin
from django.utils.html import format_html
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.safestring import mark_safe
from .models import SpecialEvents, BusinessPartner, EventGallery, CustomerPhotoDownload
from .actions import active_list_of_special_events, deactive_list_of_special_events
from .forms import EventGalleryForm
# from .forms import BulkEventGalleryUploadForm  # Temporarily disabled
from .utils import process_gallery_image, generate_unique_filename


@admin.register(SpecialEvents)
class SpecialAdmin(admin.ModelAdmin):
    model = SpecialEvents
    filter_horizontal = ('event',)
    search_fields = ('name_special_event_list',)
    autocomplete_fields = ['event']
    list_display = ['name_special_event_list', 'special_events', 'active_list']
    actions = [active_list_of_special_events, deactive_list_of_special_events]


@admin.register(BusinessPartner)
class BusinessPartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'is_active', 'display_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'email']
    list_editable = ['is_active', 'display_order']
    ordering = ['display_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active', 'display_order')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'website')
        }),
        ('Logo', {
            'fields': ('logo',)
        }),
    )


@admin.register(EventGallery)
class EventGalleryAdmin(admin.ModelAdmin):
    list_display = ['thumbnail_preview', 'event', 'title', 'is_featured', 'is_public', 'download_count', 'uploaded_at']
    list_filter = ['is_featured', 'is_public', 'uploaded_at', 'event']
    search_fields = ['title', 'description', 'event__name']
    list_editable = ['is_featured', 'is_public']
    ordering = ['-uploaded_at']
    readonly_fields = ['download_count', 'uploaded_at', 'image_preview']
    form = EventGalleryForm
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('event', 'title', 'description', 'photo', 'image_preview', 'thumbnail')
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_public', 'uploaded_by')
        }),
        ('Statistics', {
            'fields': ('download_count', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    # def get_urls(self):
    #     urls = super().get_urls()
    #     custom_urls = [
    #         path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='shop_eventgallery_bulk_upload'),
    #     ]
    #     return custom_urls + urls
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('event', 'uploaded_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">',
                obj.thumbnail.url
            )
        elif obj.photo:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;">',
                obj.photo.url
            )
        return "No image"
    thumbnail_preview.short_description = "Preview"
    
    def image_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 8px;">',
                obj.photo.url
            )
        return "No image"
    image_preview.short_description = "Image Preview"
    
    
    # Bulk upload functionality temporarily disabled due to Django 3.2 multiple file upload limitations
    # def bulk_upload_view(self, request):
    #     # Implementation temporarily disabled
    #     pass
    
    # def process_bulk_upload(self, request, form):
    #     # Implementation temporarily disabled  
    #     pass


@admin.register(CustomerPhotoDownload)
class CustomerPhotoDownloadAdmin(admin.ModelAdmin):
    list_display = ['customer', 'gallery_photo', 'downloaded_at']
    list_filter = ['downloaded_at', 'gallery_photo__event']
    search_fields = ['customer__email', 'gallery_photo__title', 'gallery_photo__event__name']
    ordering = ['-downloaded_at']
    readonly_fields = ['download_token', 'downloaded_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('customer', 'gallery_photo', 'gallery_photo__event')
