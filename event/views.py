from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from event.forms import EventForm, TicketForm
from event.models import Event, Ticket


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
            tickets = Ticket.objects.filter(event=events.pk)
            return render(request, 'ticket_type_list.html', {'tickets': tickets})
    else:
        form = EventForm()
    return render(request, 'event_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def event_update(request, event_id):
    tickets = Ticket.objects.filter(event=event_id)
    instance = get_object_or_404(Event, id=event_id)
    if request.method == 'GET':
        form = EventForm(instance=instance)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('events_promoter')
    return render(request, 'event_create.html', {'form': form, 'tickets': tickets})


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
    return render(request, 'ticket_type_list.html', {'tickets': tickets})


@login_required(login_url='/promoter/account/login/')
def ticket_type_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = Ticket(**form.cleaned_data)
            ticket.save()
            tickets = Ticket.objects.filter(event=ticket.event_id)
            return render(request, 'ticket_type_list.html', {'tickets': tickets})
            # return redirect('ticket_type_list')
    else:
        form = TicketForm()
    return render(request, 'ticket_type_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def ticket_type_update(request, ticket_id):
    instance = get_object_or_404(Ticket, id=ticket_id)
    if request.method == 'GET':
        form = TicketForm(instance=instance)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            tickets = Ticket.objects.filter(event=instance.event_id)
            return render(request, 'ticket_type_list.html', {'tickets': tickets})
    return render(request, 'ticket_type_create.html', {'form': form})


