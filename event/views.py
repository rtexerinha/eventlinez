from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, Paginator, InvalidPage
from django.shortcuts import render, redirect, get_object_or_404

from event.forms import EventForm, TicketForm, VendorForm
from event.models import Event, Ticket
from event.models import Vendor


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
            event = Event(**form.cleaned_data)
            event.promoter = request.user.promoter
            event.save()
            tickets = Ticket.objects.filter(event=event.pk)
            return render(request, 'ticket_type_list.html', {'tickets': tickets, 'event_id': event.pk})
    else:
        form = EventForm()
    return render(request, 'event_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def event_update(request, event_id):
    form = None
    form_vendor = None
    vendors = Vendor.objects.filter(promoter=request.user.promoter.id, event=event_id)
    vendors_without_event = Vendor.objects.filter(promoter=request.user.promoter.id).exclude(event=event_id)
    tickets = Ticket.objects.filter(event=event_id)
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'GET':
        form = EventForm(instance=event)
        form_vendor = VendorForm()
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect('events_promoter')
    return render(request, 'event_update.html',
                  {'form': form, 'tickets': tickets,
                   'vendors': vendors,
                   'event': event,
                   'form_vendor': form_vendor,
                   'vendors_without_event': vendors_without_event})


@login_required(login_url='/promoter/account/login/')
def event_remove(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('events_promoter')


@login_required(login_url='/promoter/account/login/')
def ticket_type_list(request):
    tickets = Ticket.objects.all()
    return render(request, 'ticket_type_list.html', {'tickets': tickets})


@login_required(login_url='/promoter/account/login/')
def ticket_type_list_per_event(request, event_id):
    tickets = Ticket.objects.filter(event=event_id)
    return render(request, 'ticket_type_list.html', {'tickets': tickets, 'event_id': event_id})


@login_required(login_url='/promoter/account/login/')
def ticket_type_create(request, event_id):
    if request.method == 'POST':
        form = TicketForm(data=request.POST)
        if form.is_valid():
            ticket = Ticket(**form.cleaned_data)
            # ticket.event = Event.objects.filter(id=event_id)
            ticket.save()
            tickets = Ticket.objects.filter(event__id=event_id)
            return render(request, 'ticket_type_list.html', {'tickets': tickets, 'event_id': event_id})
            # return redirect('ticket_type_list')
    else:
        form = TicketForm(event_id)
    return render(request, 'ticket_type_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def ticket_type_update(request, ticket_id):
    form = None
    instance = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'GET':
        form = TicketForm(event_id=instance.event_id, instance=instance)
    if request.method == 'POST':
        form = TicketForm(event_id=instance.event_id, data=request.POST, instance=instance)
        if form.is_valid():
            form.save()
            tickets = Ticket.objects.filter(event=instance.event_id)
            return render(request, 'ticket_type_list.html', {'tickets': tickets, 'event_id': instance.event_id})
    return render(request, 'ticket_type_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def vendors_list(request):
    vendors = Vendor.objects.filter(promoter=request.user.promoter.id)
    return render(request, 'vendors_list.html', {'vendors': vendors})


@login_required(login_url='/promoter/account/login/')
def vendor_create(request):
    if request.method == 'POST':
        form_vendor = VendorForm(data=request.POST)
        if form_vendor.is_valid():
            vendor = Vendor(**form_vendor.cleaned_data)
            vendor.promoter = request.user.promoter
            vendor.save()
            return redirect('vendors_list')
    else:
        form_vendor = VendorForm()
    return render(request, 'vendor_create.html', {'form_vendor': form_vendor})


@login_required(login_url='/promoter/account/login/')
def vendor_create_per_event(request, event_id):
    if request.method == 'POST':
        event = Event.objects.get(id=event_id)
        form_vendor = VendorForm(data=request.POST)
        if form_vendor.is_valid():
            vendor = Vendor(**form_vendor.cleaned_data)
            vendor.promoter = request.user.promoter
            vendor.save()
            vendor.event_set.add(event)
            return redirect('update_event', event_id=event_id)
    else:
        form_vendor = VendorForm()
    return render(request, 'vendor_create.html', {'form_vendor': form_vendor})


@login_required(login_url='/promoter/account/login/')
def vendor_update_per_event(request, event_id):
    vendor = None
    event = Event.objects.get(id=event_id)
    if request.method == "POST":
        vendor_id = request.POST.get('vendors_choice')
        vendor = Vendor.objects.get(id=vendor_id)
        vendor.event_set.add(event)
        return redirect('update_event', event_id=event_id)
    form_vendor = VendorForm()
    return render(request, 'vendor_create.html', {'form_vendor': form_vendor, 'vendor_select': vendor})


@login_required(login_url='/promoter/account/login/')
def vendors_reports(request):
    from .models import SalesByVendor
    tickets = None
    selected_event = None

    if request.method == "POST":
        event_id = request.POST.get('events_choice')
        if event_id:
            tickets = SalesByVendor.objects.filter(event=event_id)
    events = Event.objects.filter(promoter=request.user.promoter).order_by('-created')
    return render(request, 'vendors_reports.html', {
        'tickets': tickets,
        'events': events,
        'selected_event': selected_event
        })


@login_required(login_url='/promoter/account/login/')
def vendor_update(request, vendor_id):
    form_vendor = None
    vendors = Vendor.objects.get(id=vendor_id)
    if request.method == 'GET':
        form_vendor = VendorForm(instance=vendors)
        form_vendor.fields['first_name'].widget.attrs['disabled'] = 'disabled'
        form_vendor.fields['last_name'].widget.attrs['disabled'] = 'disabled'
    if request.method == 'POST':
        form_vendor = VendorForm(request.POST, instance=vendors)
        if form_vendor.is_valid():
            form_vendor.save()
            return redirect('vendors_list')
    return render(request, 'vendor_create.html', {'form_vendor': form_vendor, 'vendors': vendors})


@login_required(login_url='/promoter/account/login/')
def vendor_remove(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.delete()
    return redirect('vendors_list')
