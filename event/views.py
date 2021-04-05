import xlsxwriter
from io import BytesIO
from os import path

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import StreamingHttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import ugettext

from event.forms import EventForm
from event.models import Event, Ticket
from .models import Promoter
from .forms import PromoterForm, ResetPasswordForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages


@login_required(login_url='/promoter/account/login/')
def event_list(request):
    promoter = request.user.promoter.id
    events = Event.objects.filter(promoter=promoter).order_by('-created')
    return render(request, 'events_list.html', {'events': events})


@login_required(login_url='/promoter/account/login/')
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            events = Event(**form.cleaned_data)
            events.promoter = request.user.promoter
            events.save()
            return redirect('events_promoter')
    else:
        form = EventForm()
    return render(request, 'event_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def event_update(request, event_id):
    instance = get_object_or_404(Event, id=event_id)
    if request.method == 'GET':
        form = EventForm(instance=instance)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('events_promoter')
    return render(request, 'event_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def event_remove(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('events_promoter')


@login_required(login_url='/promoter/account/login/')
def tickets_list(request):
    events = Event.objects.filter(promoter=request.user.promoter).order_by('-created')
    tickets = Ticket.objects.filter(event__promoter=request.user.promoter).order_by('-id')
    selected_event = None
    if request.method == "POST":
        event_id = request.POST.get('events_choice')
        if event_id:
            selected_event = Event.objects.get(pk=event_id)
            tickets = tickets.filter(event=selected_event)
    paginator = Paginator(tickets, 6)
    page = int(request.GET.get('page', '1'))
    try:
        tickets = paginator.page(page)
    except (EmptyPage, InvalidPage):
        tickets = paginator.page(paginator.num_pages)
    data = {'tickets': tickets, 'events': events, 'selected_event': selected_event}
    return render(request, 'ticket_list.html', data)


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
    title = book.add_format(props_title)
    tthead = book.add_format(props_header)
    event_style = book.add_format(props_event)
    tbody_style = book.add_format(props_table)
    money_format = book.add_format(props_price)

    sheet.set_column('B:B', 40)
    sheet.set_column('D:E', 20)
    sheet.set_row(1, 25)
    sheet.set_default_row(30)
    sheet.merge_range('A1:E1', u"{0}".format(ugettext("Tickets Sold")), title)

    if event_id:
        tickets = Ticket.objects.filter(event_id=event_id).values_list('id',
                                                                       'event__name',
                                                                       'order_item__price',
                                                                       'created_at',
                                                                       'customer__first_name',
                                                                       'customer__last_name'
                                                                       ).order_by('-id')
    else:
        tickets = Ticket.objects.filter(event__promoter=request.user.promoter). \
            values_list('id', 'event__name', 'order_item__price', 'created_at', 'customer__first_name',
                        'customer__last_name').order_by('-id')

    row_num = 1
    columns = ['Ticket', 'Event', 'Price', 'Date', 'First Name', 'Last Name']
    for col_num in range(len(columns)):
        sheet.write(row_num, col_num, columns[col_num], tthead)

    for idx, data in enumerate(tickets):
        row = 2 + idx
        sheet.write_number(row, 0, data[0], tbody_style)
        sheet.write_string(row, 1, data[1], event_style)
        sheet.write_number(row, 2, data[2], money_format, )
        sheet.write(row, 3, data[3].strftime('%Y-%m-%d %H:%M'), tbody_style)
        sheet.write_string(row, 4, data[4], tbody_style)
        sheet.write_string(row, 5, data[5], tbody_style)

    way = path.abspath("static")
    logo = path.join(way, 'img', 'logo.png')
    sheet.insert_image('A1', logo)

    book.close()
    output.seek(0)
    return response


@login_required(login_url='/promoter/account/login/')
def update_promoter(request):
    user_id = request.user.id
    promoter = Promoter.objects.get(user_id=user_id)
    form = PromoterForm(instance=promoter)

    if request.method == 'POST':
        form = PromoterForm(request.POST, instance=promoter)

        if form.is_valid():
            form.save()
            return redirect('events_promoter')
        else:
            return render(request, 'update_promoter.html', {'form': form})
    elif request.method == 'GET':
        return render(request, 'update_promoter.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def reset_password(request):

    if request.method == 'POST':
        form = ResetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')

            return redirect('events_promoter')

        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ResetPasswordForm(request.user)
    return render(request, 'reset_password.html', {
        'form': form
    })
