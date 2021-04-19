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
        event_list = Event.objects.filter(category=c_page, available=True)
    else:
        now = datetime.now()
        future_events = Event.objects.all().filter(available=True, event_date__gte=now).order_by('event_date')
        old_events = Event.objects.all().filter(available=True, event_date__lt=now).order_by('-event_date')
        # event_list = future_events | old_events
        event_list = list(itertools.chain(future_events, old_events))
    paginator = Paginator(event_list, 8)
    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1
    try:
        events = paginator.page(page)
    except (EmptyPage, InvalidPage):
        events = paginator.page(paginator.num_pages)
    return render(request, 'shop/home.html', {'category': c_page, 'events': events})


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
