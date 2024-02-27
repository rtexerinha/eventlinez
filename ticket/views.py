from __future__ import unicode_literals

from datetime import datetime
from datetime import timedelta
from io import BytesIO
from os import path

import xlsxwriter
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.db.models import Q

from event.models import Event
from ticket.models import Ticket, FreeTicket


@login_required(login_url='/promoter/account/login/')
def ticket_checkin(request, checkin):
    # host = request.get_raw_uri().replace(request.get_full_path(), "")
    if not hasattr(request.user, "promoter"):
        error_msg = "You are not authorized to validate this ticket!"
        return render(request, 'pages/error401.html', {'error_msg': error_msg})
    errors = []

    ticket = Ticket.objects.get(event_ticket__event__promoter=request.user.promoter, uuid=checkin)
    if not ticket:
        errors.append('Ticket does not belong to this promoter.')
    ticket_date_event = ticket.event_ticket.event.event_date
    deadline = (ticket_date_event + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
    if datetime.now().strftime("%Y-%m-%d %H:%M:%S") > deadline:
        errors.append('Deadline to check in is over')
    if ticket.checkin_date is not None:
        errors.append('Ticket has already been validated!')
    if errors is not None and len(errors):
        return render(request, 'ticket/ticket_checkin_error.html', {'errors': errors})
    ticket.checkin_date = datetime.now()
    ticket.save()
    tickets = Ticket.objects.filter(event_ticket__event__promoter=request.user.promoter,
                                    event_ticket=ticket.event_ticket,
                                    checkin_date__isnull=False).order_by('-checkin_date')
    return render(request, 'ticket/ticket_checkin.html', {'tickets': tickets})


@login_required(login_url='/promoter/account/login/')
def search_checkin(request):
    tickets = None
    query = None
    if 'q' in request.GET:
        query = request.GET.get('q')
        ticket = Ticket.objects.filter(event_ticket__event__promoter=request.user.promoter)
        tickets = ticket.all().filter(
            Q(guest_name__icontains=query) | Q(id__icontains=query))
    return render(request, 'ticket/ticket_checkin.html', {'query': query, 'tickets': tickets})


@login_required(login_url='/promoter/account/login/')
def search_ticket_sold(request):
    q = None
    tickts = None
    if 'query' in request.GET:
        q = request.GET.get('query')
        ticket = Ticket.objects.filter(event_ticket__event__promoter=request.user.promoter)
        tickts = ticket.all().filter(
            Q(guest_name__icontains=q) | Q(id__icontains=q))
    return render(request, 'ticket/ticket_sold_list.html', {'query': q, 'tickets': tickts})


@login_required(login_url='/promoter/account/login/')
def tickets_validate(request):
    from ticket.models import Ticket
    selected_event = None
    events = Event.objects.filter(promoter=request.user.promoter).order_by('-created')
    tickets = Ticket.objects.filter(event_ticket__event__promoter=request.user.promoter,
                                    checkin_date__isnull=False).order_by('-id')
    if request.method == "POST":
        event_id = request.POST.get('events_choice')
        if event_id:
            selected_event = Event.objects.get(pk=event_id)
            tickets = tickets.filter(event_ticket__event=selected_event)
    paginator = Paginator(tickets, 9)
    page = int(request.GET.get('page', '1'))
    try:
        tickets = paginator.page(page)
    except (EmptyPage, InvalidPage):
        tickets = paginator.page(paginator.num_pages)
    data = {'tickets': tickets, 'events': events, 'selected_event': selected_event}
    return render(request, 'ticket/ticket_checkin.html', data)


@login_required(login_url='/promoter/account/login/')
def ticket_qrcode(request):
    ticket_uuid = request.GET['tkt']
    try:
        ticket = Ticket.objects.get(uuid=ticket_uuid)
    except:
        ticket = FreeTicket.objects.get(uuid=ticket_uuid)
    svg = ticket.as_qrcode()
    return render(request, "ticket/ticket_qrcode.html", {'svg': svg, 'ticket': ticket})


@login_required(login_url='/promoter/account/login/')
def tickets_sold_list(request):
    from ticket.models import Ticket
    events = Event.objects.filter(promoter=request.user.promoter).order_by('-created')
    tickets = Ticket.objects.filter(event_ticket__event__promoter=request.user.promoter).order_by('-id')
    selected_event = None
    if request.method == "POST":
        event_id = request.POST.get('events_choice')
        if event_id:
            selected_event = Event.objects.get(pk=event_id)
            tickets = tickets.filter(event_ticket__event=selected_event)
    paginator = Paginator(tickets, 20)
    page = int(request.GET.get('page', '1'))
    try:
        tickets = paginator.page(page)
    except (EmptyPage, InvalidPage):
        tickets = paginator.page(paginator.num_pages)
    data = {'tickets': tickets, 'events': events, 'selected_event': selected_event}
    return render(request, 'ticket/ticket_sold_list.html', data)


@login_required(login_url='/promoter/account/login/')
def tickets_excel(request, event_id=None):
    output = BytesIO()
    response = StreamingHttpResponse(
        output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=tickets.xlsx'

    book = xlsxwriter.Workbook(output)
    sheet = book.add_worksheet("Tickets List")
    sheet.set_tab_color('#FF9900')  # Orange

    props_title = {'bold': True, 'font_size': 14, 'align': 'center',
                   'valign': 'vcenter', 'font_name': 'Arial'}

    props_header = {'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                    'color': '#171717', 'bg_color': '#F4F4F4', 'font_name': 'Arial'}

    props_price = {'num_format': '[$$-409]#,##0.00', 'font_size': 10, 'align': 'right', 'color': '#171717',
                   'bg_color': '#FFFFFF', 'font_name': 'Arial', 'bottom': 1,
                   'bottom_color': '#dee2e6', 'valign': 'vcenter'}

    props_event = {'font_size': 10, 'align': 'left', 'color': '#171717', 'bg_color': '#FFFFFF',
                   'font_name': 'Arial', 'bottom': 1, 'bottom_color': '#dee2e6', 'valign': 'vcenter'}

    props_table = {'font_size': 10, 'align': 'center', 'color': '#171717', 'bg_color': '#FFFFFF',
                   'font_name': 'Arial', 'bottom': 1, 'bottom_color': '#dee2e6', 'valign': 'vcenter'}
    # Styles
    title_format = book.add_format(props_title)
    tthead = book.add_format(props_header)
    event_style = book.add_format(props_event)
    tbody_style = book.add_format(props_table)
    money_format = book.add_format(props_price)

    sheet.set_column('B:B', 40)
    sheet.set_column('C:C', 40)
    sheet.set_column('E:F', 20)
    sheet.set_column('G:G', 40)
    sheet.set_row(1, 25)
    sheet.set_default_row(30)
    sheet.merge_range('A1:F1', u"", title_format)

    if event_id:
        selected_event = Event.objects.get(pk=event_id)
        tickets = Ticket.objects.filter(event_ticket__event=selected_event).values_list(
            'id', 'event_ticket__event__name', 'event_ticket__name', 'order_item__unit_price',
            'order_item__promo_code', 'created_at', 'guest_name').order_by('-id')
    else:
        tickets = Ticket.objects.filter(
            event_ticket__event__promoter=request.user.promoter).values_list(
            'id', 'event_ticket__event__name', 'event_ticket__name', 'order_item__unit_price',
            'order_item__promo_code', 'created_at', 'guest_name').order_by('-id')
    row_num = 1
    columns = ['Ticket', 'Event', 'Type ticket', 'Price', 'Promo Code', 'Date', 'Guest Name']
    for col_num in range(len(columns)):
        sheet.write(row_num, col_num, columns[col_num], tthead)

    for idx, data in enumerate(tickets):
        row = 2 + idx
        sheet.write_number(row, 0, data[0], tbody_style)
        sheet.write_string(row, 1, data[1], event_style)
        sheet.write_string(row, 2, data[2], event_style)
        sheet.write_number(row, 3, data[3], money_format, )

        if data[4] is None:
            sheet.write_string(row, 4, '', tbody_style, )
        else:
            sheet.write_string(row, 4, data[4], tbody_style, )
        sheet.write(row, 5, data[5].strftime('%Y-%m-%d %H:%M'), tbody_style)
        if data[6] is None:
            sheet.write_string(row, 6, '', tbody_style)
        else:
            sheet.write_string(row, 6, data[6], tbody_style)

    way = path.abspath("static")
    logo = path.join(way, 'img', 'logo.png')
    sheet.insert_image('A1', logo)

    book.close()
    output.seek(0)
    return response
