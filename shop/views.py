import logging
from datetime import datetime
import itertools

from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.http import BadHeaderError, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from event.models import Category, Event
from .forms import ContactForm

logger = logging.getLogger(__name__)


def about(request):
    return render(request, 'pages/about.html')


def index(request, c_slug=None):
    c_page = None
    if c_slug is not None:
        c_page = get_object_or_404(Category, slug=c_slug)
    lis = lists_events(c_slug)
    page = pagination_home(request, lis)
    detach = Event.objects.all().filter(available=True).order_by('-event_date').first()
    return render(request, 'shop/home.html', {'detach': detach,
                                              'category': c_page,
                                              'events_futures': page[0],
                                              'events_old': page[1],
                                              'events_all': page[2]})


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
        pagin.append(Paginator(lists[1], 4))
        try:
            events_future = pagin[0].page(pag)
            events_old = pagin[1].page(pages)
        except (EmptyPage, InvalidPage):
            events_future = pagin[0].page(pagin[0].num_pages)
            events_old = pagin[1].page(pagin[1].num_pages)
    eventsListsOfLists = [events_future, events_old, events_all]
    return eventsListsOfLists


def terms(request):
    return render(request, 'pages/terms.html')


def contact(request):
    if request.method == 'GET':
        form = ContactForm()
        return render(request, 'pages/contactus.html', {'form': form})
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
                fail_silently=False,
                html_message=html_message
            )
        except BadHeaderError:
            return HttpResponse('Invalid header found.')
        return redirect('shop:index')
    return render(request, 'pages/contactus.html', {'form': form})


def product_event_detail(request, c_slug, event_slug):
    try:
        event = Event.objects.get(category__slug=c_slug, slug=event_slug)
        products_list = Event.objects.all().filter(available=True)
    except Exception as e:
        raise e
    return render(request, 'shop/event.html', {'event': event, 'products_list': products_list})


def event_detail_new(request, c_slug, event_slug):
    try:
        event = Event.objects.get(category__slug=c_slug, slug=event_slug)
        events_list = Event.objects.all().filter(available=True)
    except Exception as e:
        raise e
    return render(request, 'shop/event-new.html', {'event': event, 'products_list': events_list})


def search_result(request):
    events = None
    query = None
    if 'q' in request.GET:
        query = request.GET.get('q')
        events = Event.objects.all().filter(
            Q(name__icontains=query) | Q(description__icontains=query))
    return render(request, 'search.html', {'query': query, 'events': events})


def handler404(request, exception):
    return render(request, 'pages/error.html')


def handler500(request, *args, **argv):
    return render(request, 'pages/500.html', status=500)
