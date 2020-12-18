import csv

import xlsxwriter
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext

from event.forms import NewEvent, UpdateEvent
from event.models import Event, Ticket
from order.models import Order


@login_required(login_url='/promoter/account/login/')
def order_promoter(request):
    promoter = request.user.promoter
    orders = Order.objects.filter(orderitem__event__promoter=promoter).order_by('-id')
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
    events = Event.objects.filter(promoter=promoter).order_by('-created')
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
    tickets = Ticket.objects.filter(event_id=event_id).order_by('-id')
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


def tickets_excel(request):
    output = BytesIO()
    response = StreamingHttpResponse(
        output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=tickets.xlsx'

    book = xlsxwriter.Workbook(output)
    sheet = book.add_worksheet("Tickets List")
    sheet.set_tab_color('#FF9900')  # Orange

    # Styles

    title = book.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
    tthead = book.add_format({'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                              'color': '#171717', 'bg_color': '#F4F4F4'})
    tbody = book.add_format({'font_size': 10, 'align': 'left', 'color': '#171717', 'bg_color': '#FFFFFF', 'bottom': 1})

    tbody.set_bottom_color('#dee2e6')

    title.set_font_name('Arial')
    sheet.set_column('B:B', 40)
    sheet.set_column('C:D', 20)
    sheet.merge_range('A2:D2', u"{0}".format(ugettext("Tickets Sold")), title)

    tickets = Ticket.objects.filter(event__promoter=request.user.promoter).values_list('id',
                                                                                       'event__name',
                                                                                       'created_at',
                                                                                       'customer__first_name'
                                                                                       ).order_by('-id')

    row_num = 2
    columns = ['ID', 'Event', 'created_at', 'Customer']
    for col_num in range(len(columns)):
        sheet.write(row_num, col_num, columns[col_num], tthead)

    for idx, data in enumerate(tickets):
        row = 3 + idx
        sheet.write_number(row, 0, data[0], tbody)
        sheet.write_string(row, 1, data[1], tbody)
        sheet.write(row, 2, data[2].strftime('%Y-%m-%d %H:%M'), tbody)
        sheet.write_string(row, 3, data[3], tbody)

    book.close()
    output.seek(0)
    return response
