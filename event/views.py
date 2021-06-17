from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from event.forms import EventForm, TicketForm
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
            return redirect('ticket_type_list')
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
def ticket_type_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = Ticket(**form.cleaned_data)
            ticket.save()
            return redirect('ticket_type_list')
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
            return redirect('ticket_type_list')
    return render(request, 'ticket_type_create.html', {'form': form})


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
