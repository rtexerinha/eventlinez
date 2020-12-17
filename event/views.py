import csv

import xlsxwriter
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from event.forms import NewEvent, UpdateEvent
from event.models import Event, Ticket
from order.models import Order


@login_required(login_url='/promoter/account/login/')
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
    tickets = Ticket.objects.filter(event__promoter=promoter).order_by('-id')
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
    if request.method == 'POST':
        form = NewEvent(request.POST, request.FILES)
        if form.is_valid():
            events = Event(**form.cleaned_data)
            events.promoter = request.user.promoter
            events.save()
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


def get_foo_table_data():
    """
    Some table data
    """
    return [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ]


def tickets_excel(request):

    output = BytesIO()
    book = xlsxwriter.Workbook(output)
    sheet = book.add_worksheet("Tickets List")
    promoter = request.user.promoter
    tickets = Ticket.objects.filter(event__promoter=promoter).values_list('id',
                                                                          'event__name',
                                                                          'customer__first_name',
                                                                          'order_item_id')

    for row, columns in enumerate(tickets):
        for column, cell_data in enumerate(columns):
            sheet.write(row, column, cell_data)

    book.close()  # close book and save it in "output"
    output.seek(0)  # seek stream on begin to retrieve all data from it
    response = StreamingHttpResponse(
        output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=tickets.xlsx'
    return response
