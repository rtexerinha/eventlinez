from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import EventGallery, Event
import os
import uuid


@staff_member_required
def bulk_upload_view(request):
    """Standalone bulk upload view that handles multiple files properly"""
    
    if request.method == 'POST':
        return handle_bulk_upload(request)
    
    # GET request - show the upload form
    events = Event.objects.all().order_by('-created')
    
    context = {
        'events': events,
        'title': 'Bulk Upload Gallery Photos',
    }
    
    return render(request, 'admin/shop/eventgallery/simple_bulk_upload.html', context)


@csrf_exempt
def handle_bulk_upload(request):
    """Handle the actual file uploads"""
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    # Check authentication manually to return JSON error instead of redirect
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Authentication required. Please login as staff.'}, status=401)
    
    # Get form data
    event_id = request.POST.get('event_id')
    title_prefix = request.POST.get('title_prefix', '')
    description = request.POST.get('description', '')
    is_featured = request.POST.get('is_featured') == 'on'
    is_public = request.POST.get('is_public', 'on') == 'on'
    
    # Validate event
    try:
        event = Event.objects.get(id=event_id)
    except (Event.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid event selected'}, status=400)
    
    # Get uploaded files
    uploaded_files = request.FILES.getlist('photos')
    
    if not uploaded_files:
        return JsonResponse({'error': 'No files were uploaded'}, status=400)
    
    # Process files
    success_count = 0
    error_count = 0
    errors = []
    
    for i, uploaded_file in enumerate(uploaded_files, 1):
        try:
            # Validate file
            if not uploaded_file.content_type.startswith('image/'):
                errors.append(f'File "{uploaded_file.name}" is not an image')
                error_count += 1
                continue
            
            if uploaded_file.size > 20 * 1024 * 1024:  # 20MB limit
                errors.append(f'File "{uploaded_file.name}" is too large (max 20MB)')
                error_count += 1
                continue
            
            # Generate title
            if title_prefix:
                title = f"{title_prefix} {i}"
            else:
                title = f"{event.name} - Photo {i}"
            
            # Create EventGallery instance
            gallery_photo = EventGallery(
                event=event,
                title=title,
                description=description,
                photo=uploaded_file,
                is_featured=is_featured,
                is_public=is_public,
                uploaded_by=request.user
            )
            
            gallery_photo.save()
            success_count += 1
            
        except Exception as e:
            errors.append(f'Error uploading "{uploaded_file.name}": {str(e)}')
            error_count += 1
    
    # Return JSON response
    return JsonResponse({
        'success': True,
        'message': f'Successfully uploaded {success_count} photos',
        'success_count': success_count,
        'error_count': error_count,
        'errors': errors
    })


@staff_member_required  
def bulk_upload_success(request):
    """Success page after bulk upload"""
    success_count = request.GET.get('success_count', 0)
    error_count = request.GET.get('error_count', 0)
    
    context = {
        'success_count': success_count,
        'error_count': error_count,
        'title': 'Upload Complete'
    }
    
    return render(request, 'admin/shop/eventgallery/upload_success.html', context)
