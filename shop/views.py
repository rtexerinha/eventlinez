import logging
from datetime import datetime
import itertools
import os
import uuid
from django.http import FileResponse, Http404
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
    featured_gallery = EventGallery.objects.filter(is_public=True, is_featured=True).select_related('event').order_by('-uploaded_at')[:6]
    
    return render(request, 'shop/home.html', {'detachs': detachs,
                                              'category': c_page,
                                              'events_futures': page[0],
                                              'events_old': page[1],
                                              'events_all': page[2],
                                              'business_partners': business_partners,
                                              'featured_gallery': featured_gallery,
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
        return render(request, 'pages/contactus.html', {'form': form, 'PROD': settings.PROD})
    form = ContactForm(request.POST)
    if form.is_valid():
        subject = form.cleaned_data['subject']
        cellphone = form.cleaned_data['cellphone']
        mail = form.cleaned_data['mail']
        message = form.cleaned_data['message']

        subject_select = "Subject: {0}".format(subject)
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
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return redirect('shop:index')
    return render(request, 'pages/contactus.html', {'form': form})


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
    """Display all public gallery photos"""
    gallery_photos = EventGallery.objects.filter(
        is_public=True
    ).select_related('event').order_by('-uploaded_at')
    
    # Add pagination
    paginator = Paginator(gallery_photos, 12)
    page_number = request.GET.get('page')
    photos = paginator.get_page(page_number)
    
    context = {
        'gallery_photos': photos,
        'PROD': settings.PROD
    }
    return render(request, 'shop/gallery/gallery_home.html', context)
