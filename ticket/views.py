import xlsxwriter
from io import BytesIO
from os import path
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import StreamingHttpResponse
from ticket.models import Ticket
from event.models import Event
import qrcode
import qrcode.image.svg


@login_required(login_url='/promoter/account/login/')
def ticket_checkin(request, checkin):
    host = request.get_raw_uri().replace(request.get_full_path(), "")
    if not hasattr(request.user, "promoter"):
        return HttpResponse("You are authorized to checkin ticket!", status=401)

    return HttpResponse('Success: ' + host + str(checkin))


def ticket_qrcode(request):
    context = {}
    # host = request.get_raw_uri().replace(request.get_full_path(), "")
    img = qrcode.make("host;dieudyeuiydhie", image_factory=qrcode.image.svg.SvgImage, box_size=20)
    uiid = "8755dce1-f139-4068-95a4-0dd823ac5890"
    ticket = Ticket.objects.get(uuid=uiid)
    # img = ticket.qrcode_ticket()
    stream = BytesIO()
    img.save(stream)
    context["svg"] = stream.getvalue().decode()
    return render(request, "ticket/qr.html", context=context)


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
    return render(request, 'ticket_sold_list.html', data)


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
    columns = ['Ticket', 'Event', 'Type ticket', 'Price', 'Promo Code',  'Date', 'Guest Name']
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
