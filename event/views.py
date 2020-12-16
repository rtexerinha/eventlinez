import csv

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from event.forms import NewEvent, UpdateEvent
from event.models import Event, Ticket
from order.models import Order


@login_required(login_url='account/login/')
def order_promoter(request):
    promoter = request.user.promoter
    orders = Order.objects.filter(orderitem__event__promoter=promoter)
    paginator = Paginator(orders, 8)
    page = int(request.GET.get('page', '1'))
    try:
        orders = paginator.page(page)
    except (EmptyPage, InvalidPage):
        orders = paginator.page(paginator.num_pages)
    return render(request, 'orders_list.html', {'orders': orders})


@login_required(login_url='/promoter/account/login/')
def events_promoter(request):
    promoter = request.user.promoter.id
    events = Event.objects.filter(promoter=promoter)
    return render(request, 'events_list.html', {'events': events})


@login_required(login_url='/promoter/account/login/')
def tickets_list(request):
    promoter = request.user.promoter
    tickets = Ticket.objects.filter(event__promoter=promoter)
    paginator = Paginator(tickets, 12)
    page = int(request.GET.get('page', '1'))
    try:
        tickets = paginator.page(page)
    except (EmptyPage, InvalidPage):
        tickets = paginator.page(paginator.num_pages)
    return render(request, 'ticket_list.html', {'tickets': tickets})


@login_required(login_url='/promoter/account/login/')
def tickets_list_events(request, event_id):
    tickets = Ticket.objects.filter(event_id=event_id)
    paginator = Paginator(tickets, 6)
    page = int(request.GET.get('page', '1'))
    try:
        tickets = paginator.page(page)
    except (EmptyPage, InvalidPage):
        tickets = paginator.page(paginator.num_pages)
    return render(request, 'ticket_list.html', {'tickets': tickets})


@login_required(login_url='/promoter/account/login/')
def new_events(request):
    promoter = request.user.promoter
    if request.method == 'POST':
        form = NewEvent(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            unit_price = form.cleaned_data['unit_price']
            stock = form.cleaned_data['stock']
            category = form.cleaned_data['category']
            description = form.cleaned_data['description']
            event_date = form.cleaned_data['event_date']
            event_address = form.cleaned_data['event_address']
            image = form.cleaned_data['image']
            available = form.cleaned_data['available']

            events = Event.objects.create(
                name=name,
                unit_price=unit_price,
                stock=stock,
                category=category,
                description=description,
                event_date=event_date,
                promoter=promoter,
                event_address=event_address,
                image=image,
                available=available,
            )
            events.save()
            print(events)
            return redirect('events_promoter')
    else:
        form = NewEvent()
    return render(request, 'event_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def update_event(request, event_id):
    instance = get_object_or_404(Event, id=event_id)
    form = UpdateEvent(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return redirect('events_promoter')
    return render(request, 'event_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def remove_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('events_promoter')


@login_required(login_url='/promoter/account/login/')
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order', 'Customer', 'Email', 'Date', 'Total'])

    orders = Order.objects.all().values_list('id', 'billingName', 'emailAddress', 'created', 'total')

    for list_order in orders:
        writer.writerow(list_order)

    return response


@login_required(login_url='/promoter/account/login/')
def tickets_csv(request):
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = 'attachment; filename="tickets.csv"'
    writer_ticket = csv.writer(resp)
    writer_ticket.writerow(['Num', 'Event', 'Created', 'Customer', 'Order'])
    promoter = request.user.promoter
    tickets = Ticket.objects.filter(event__promoter=promoter).values_list('id',
                                                                          'event__name',
                                                                          'created_at',
                                                                          'customer__first_name',
                                                                          'order_item_id')

    for ticket_list in tickets:
        writer_ticket.writerow(ticket_list)
    return resp
