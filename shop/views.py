import logging
from datetime import datetime
import itertools
import os
import uuid
from django.http import FileResponse, Http404
from django.http import JsonResponse
from django.utils import timezone

from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.http import BadHeaderError, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from event.models import Category, Event
from promoter.models import Vendor
from .forms import ContactForm
from .models import SpecialEvents, BusinessPartner, EventGallery, CustomerPhotoDownload
from django.conf import settings

# Try to import requests for reCAPTCHA validation
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


def index(request, c_slug=None):
    c_page = None
    if c_slug is not None:
        c_page = get_object_or_404(Category, slug=c_slug)
    lis = lists_events(c_slug)
    page = pagination_home(request, lis)
    detachs = SpecialEvents.objects.filter(active_list=True)
    
    # Get business partners and featured gallery photos
    business_partners = BusinessPartner.objects.filter(is_active=True).order_by('display_order', 'name')[:8]
    
    # Get gallery albums (events with photos) instead of individual photos
    from django.db.models import Count, Max, Q
    gallery_albums = Event.objects.filter(
        gallery_photos__is_public=True
    ).annotate(
        photo_count=Count('gallery_photos', filter=Q(gallery_photos__is_public=True)),
        latest_upload=Max('gallery_photos__uploaded_at')
    ).prefetch_related('gallery_photos').order_by('-latest_upload')[:6]
    
    # Add cover photo to each album and filter out albums without photos
    albums_with_photos = []
    for album in gallery_albums:
        cover_photo = album.gallery_photos.filter(is_public=True).first()
        if cover_photo:  # Only include albums that have at least one photo
            album.cover_photo = cover_photo
            albums_with_photos.append(album)
    
    gallery_albums = albums_with_photos
    
    return render(request, 'shop/home.html', {'detachs': detachs,
                                              'category': c_page,
                                              'events_futures': page[0],
                                              'events_old': page[1],
                                              'events_all': page[2],
                                              'business_partners': business_partners,
                                              'gallery_albums': gallery_albums,
                                              'PROD': settings.PROD
                                              })


def lists_events(slugs):
    now = datetime.now()
    if slugs is not None:
        c_page = get_object_or_404(Category, slug=slugs)
        future_events = Event.objects.all().filter(category=c_page, available=True,
                                                   event_date__gte=now).order_by('event_date')
        old_events = Event.objects.all().filter(category=c_page, available=True,
                                                event_date__lt=now).order_by('-event_date')
        event_list = list(itertools.chain(future_events, old_events))
    else:
        future_events = Event.objects.all().filter(available=True,
                                                   event_date__gte=now).order_by('event_date')
        old_events = Event.objects.all().filter(available=True,
                                                event_date__lt=now).order_by('-event_date')
        event_list = list(itertools.chain(future_events, old_events))

    lists_of_lists_events = [future_events, old_events, event_list]
    return lists_of_lists_events


def pagination_home(request, lists):
    events_future = []
    events_old = []
    events_all = []
    pagin = []
    if len(lists[0]) < 4:
        pagin.append(Paginator(lists[2], 4))
        try:
            page = int(request.GET.get('page', '1'))
        except:
            page = 1
        try:
            events_all = pagin[0].page(page)
        except (EmptyPage, InvalidPage):
            events_all = pagin[0].page(pagin[0].num_pages)
    else:
        try:
            pag = int(request.GET.get('pag', '1'))
            pages = int(request.GET.get('pages', '1'))
        except:
            pag = 1
            pages = 1
        pagin.append(Paginator(lists[0], 8))
        pagin.append(Paginator(lists[1], 8))
        try:
            events_future = pagin[0].page(pag)
            events_old = pagin[1].page(pages)
        except (EmptyPage, InvalidPage):
            events_future = pagin[0].page(pagin[0].num_pages)
            events_old = pagin[1].page(pagin[1].num_pages)
    eventslistsoflists = [events_future, events_old, events_all]
    return eventslistsoflists


def product_event_detail(request, c_slug, event_slug):
    vendor = None
    if 'vendor' in request.GET:
        vendor = Vendor.objects.filter(code=request.GET.get('vendor')).first()
    try:
        event = Event.objects.get(category__slug=c_slug, slug=event_slug)
    except Exception as e:
        raise e
    pathpage = request.META['PATH_INFO']
    if request.META['QUERY_STRING']:
        pathpage = pathpage + '?' + request.META['QUERY_STRING']
    response = render(request, 'shop/event.html', {'PROD': settings.PROD, 'event': event, 'vendor': vendor})
    response.set_cookie(key='backpage', value=pathpage, max_age=60)
    return response


def search_result(request):
    events = None
    query = None
    if 'q' in request.GET:
        query = request.GET.get('q')
        events = Event.objects.all().filter(
            Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'search.html', {'query': query, 'events': events, 'PROD': settings.PROD})


def about(request):
    return render(request, 'pages/about.html', {'PROD': settings.PROD})


def terms(request):
    return render(request, 'pages/terms.html', {'PROD': settings.PROD})


def contact(request):
    if request.method == 'GET':
        form = ContactForm()
        return render(request, 'pages/contactus.html', {
            'form': form, 
            'PROD': settings.PROD,
            'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
        })
    
    form = ContactForm(request.POST)
    
    # Validate reCAPTCHA
    recaptcha_response = request.POST.get('g-recaptcha-response')
    
    # Only validate reCAPTCHA if keys are configured and requests library is available
    if settings.RECAPTCHA_PUBLIC_KEY and settings.RECAPTCHA_PRIVATE_KEY and REQUESTS_AVAILABLE:
        recaptcha_verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        recaptcha_data = {
            'secret': settings.RECAPTCHA_PRIVATE_KEY,
            'response': recaptcha_response,
            'remoteip': ip
        }
        
        try:
            recaptcha_result = requests.post(recaptcha_verify_url, data=recaptcha_data)
            recaptcha_json = recaptcha_result.json()
            
            # Check if reCAPTCHA validation passed
            if not recaptcha_json.get('success', False):
                error_codes = recaptcha_json.get('error-codes', [])
                logger.warning(f"reCAPTCHA validation failed. Error codes: {error_codes}")
                messages.error(request, 'reCAPTCHA validation failed. Please try again.')
                return render(request, 'pages/contactus.html', {
                    'form': form,
                    'PROD': settings.PROD,
                    'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
                })
                
        except Exception as e:
            logger.error(f"reCAPTCHA verification error: {e}")
            messages.error(request, 'Security validation error. Please try again later.')
            return render(request, 'pages/contactus.html', {
                'form': form,
                'PROD': settings.PROD,
                'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
            })
    
    if form.is_valid():
        subject = form.cleaned_data['subject']
        cellphone = form.cleaned_data['cellphone']
        mail = form.cleaned_data['mail']
        message = form.cleaned_data['message']

        subject_select = "Contact: {0}".format(subject)
        mail_params = dict(mail=mail, cellphone=cellphone, subject=subject_select, message=message)

        msg = "# Eventlinez - New Contact \n  \n \n Mail: {0} \n Cellphone: {1} \n Subject: {2} " \
              "\n Message: {3}".format(mail, cellphone, subject_select, message)

        html_message = render_to_string('shop/email/email_contact.html', mail_params)

        try:
            send_mail(
                subject=subject_select,
                message=msg,
                from_email="noreply@eventlinez.com",
                recipient_list=["eventlinez.adm@gmail.com"],
                html_message=html_message
            )
            messages.success(request, 'Your message has been sent successfully! We will get back to you soon.')
            return redirect('shop:index')
        except BadHeaderError:
            logger.error("Invalid email header detected in contact form")
            messages.error(request, 'Invalid email content. Please check your input.')
        except Exception as e:
            logger.error(f"Failed to send contact email: {e}")
            messages.error(request, 'Failed to send message. Please try again later.')
    
    return render(request, 'pages/contactus.html', {
        'form': form,
        'PROD': settings.PROD,
        'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
    })


def handler404(request, exception):
    return render(request, 'pages/error.html')


def handler500(request, *args, **argv):
    return render(request, 'pages/500.html', status=500)


def event_gallery(request, event_slug):
    """Display gallery photos for a specific event"""
    event = get_object_or_404(Event, slug=event_slug)
    gallery_photos = EventGallery.objects.filter(
        event=event, 
        is_public=True
    ).order_by('-is_featured', '-uploaded_at')
    
    context = {
        'event': event,
        'gallery_photos': gallery_photos,
        'PROD': settings.PROD
    }
    return render(request, 'shop/gallery/event_gallery.html', context)


@login_required
def download_photo(request, photo_id):
    """Allow customers to download gallery photos"""
    try:
        customer = request.user.customer
    except:
        messages.error(request, 'You must be a registered customer to download photos.')
        return redirect('signin')
    
    gallery_photo = get_object_or_404(EventGallery, id=photo_id, is_public=True)
    
    # Check if customer has purchased tickets for this event
    has_ticket = customer.order_set.filter(
        orderitem__ticket__event=gallery_photo.event,
        status='completed'
    ).exists()
    
    if not has_ticket:
        messages.error(request, 'You must have purchased tickets for this event to download photos.')
        return redirect('event_gallery', event_slug=gallery_photo.event.slug)
    
    # Create download record
    download_token = str(uuid.uuid4())
    CustomerPhotoDownload.objects.get_or_create(
        customer=customer,
        gallery_photo=gallery_photo,
        defaults={'download_token': download_token}
    )
    
    # Increment download count
    gallery_photo.increment_download_count()
    
    # Serve the file
    if os.path.exists(gallery_photo.photo.path):
        response = FileResponse(
            open(gallery_photo.photo.path, 'rb'),
            content_type='image/jpeg'
        )
        response['Content-Disposition'] = f'attachment; filename="{gallery_photo.title or "event_photo"}.jpg"'
        return response
    else:
        raise Http404("Photo not found")


def gallery_home(request):
    """Display album grid (one cover per event) for all events with public photos"""
    from django.db.models import Count, Max, Q

    # Build album list: one entry per event with public photos
    events_with_photos = Event.objects.filter(
        gallery_photos__is_public=True
    ).annotate(
        photo_count=Count('gallery_photos', filter=Q(gallery_photos__is_public=True), distinct=True),
        latest_upload=Max('gallery_photos__uploaded_at')
    ).order_by('-latest_upload')

    # Simple pagination for albums
    paginator = Paginator(events_with_photos, 12)
    page_number = request.GET.get('page')
    albums_page = paginator.get_page(page_number)

    # Attach a cover photo for each event on the current page
    albums = []
    for ev in albums_page:
        cover_photo = ev.gallery_photos.filter(is_public=True).order_by('-is_featured', '-uploaded_at').first()
        if cover_photo:
            albums.append({
                'event': ev,
                'cover_photo': cover_photo,
                'photo_count': ev.photo_count,
            })

    context = {
        'albums_page': albums_page,
        'albums': albums,
        'PROD': settings.PROD,
    }
    return render(request, 'shop/gallery/gallery_home.html', context)


def event_photos_json(request, event_slug):
    """Return JSON list of public photos for the specified event (for lightbox)."""
    event = get_object_or_404(Event, slug=event_slug)
    photos_qs = EventGallery.objects.filter(event=event, is_public=True).order_by('-is_featured', '-uploaded_at')

    photos = []
    for p in photos_qs:
        photos.append({
            'id': p.id,
            'title': p.title or event.name,
            'thumbnail': p.thumbnail.url if p.thumbnail else (p.photo.url if p.photo else ''),
            'fullsize': p.photo.url if p.photo else '',
            'uploaded_at': p.uploaded_at.strftime('%Y-%m-%dT%H:%M:%S%z') if p.uploaded_at else '',
            'download_url': request.build_absolute_uri(
                redirect('shop:download_photo', photo_id=p.id).url
            ),
        })

    return JsonResponse({'event': {'name': event.name, 'slug': event.slug}, 'photos': photos})
