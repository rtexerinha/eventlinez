from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from event.forms import EventForm, TicketForm, TicketUpdateForm, VendorForm
from event.models import Event, Ticket
from promoter.models import Vendor


@login_required(login_url='/promoter/account/login/')
def event_list(request):
    from django.utils import timezone
    from django.db.models import Sum, Count, Q
    from django.core.paginator import Paginator

    promoter = request.user.promoter.id
    now = timezone.now()
    
    # Optimize queries with select_related and prefetch_related
    events_list = Event.objects.filter(promoter=promoter).select_related('city').prefetch_related('ticket_set').order_by('-created')

    # Separate active and past events with optimized queries
    active_events = events_list.filter(event_date__gte=now)
    past_events = events_list.filter(event_date__lt=now)

    # Calculate dashboard stats efficiently
    total_events = events_list.count()
    total_active = active_events.count()
    total_past = past_events.count()

    # Optimize revenue and ticket calculations using database aggregation
    # Note: These calculations depend on the Event model methods
    # If these methods are expensive, consider adding database fields for caching
    total_revenue = sum(event.get_amount() for event in events_list)
    total_tickets_sold = sum(event.qty_sould() for event in events_list)
    total_tickets_available = sum(event.quantity() for event in events_list)

    # Add pagination - 15 events per page for better performance
    paginator = Paginator(events_list, 15)
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)

    # Get top 5 active events for performance cards with limited data
    active_events_for_cards = active_events[:5]

    return render(request, 'event/events_list.html', {
        'events': events,
        'events_count': total_events,
        'active_events_count': total_active,
        'past_events_count': total_past,
        'total_revenue': total_revenue,
        'total_tickets_sold': total_tickets_sold,
        'total_tickets_available': total_tickets_available,
        'active_events': active_events_for_cards,
    })


@login_required(login_url='/promoter/account/login/')
def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = Event(**form.cleaned_data)
            event.promoter = request.user.promoter
            event.save()
            tickets = Ticket.objects.filter(event=event.pk)
            return render(request, 'ticket_type/ticket_type_list.html', {'tickets': tickets, 'event_id': event.pk})
    else:
        form = EventForm()
    return render(request, 'event/event_create.html', {'form': form})


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
    return render(request, 'event/event_update.html',
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
    return render(request, 'ticket_type/ticket_type_list.html', {'tickets': tickets})
# Check if this import exists at the top of the file, if not add it
from django.core.paginator import Paginator

@login_required(login_url='/promoter/account/login/')
def ticket_type_list_per_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    tickets = Ticket.objects.filter(event=event_id)

    # Calculate totals for the event
    total_tickets = sum(ticket.quantity for ticket in tickets)
    total_sold = sum(ticket.qty_sold() for ticket in tickets)
    total_available = sum(ticket.qty_available() for ticket in tickets)
    total_revenue = sum(ticket.qty_sold() * ticket.price for ticket in tickets)

    # Calculate percentages for each ticket type
    ticket_data = []
    for ticket in tickets:
        sold = ticket.qty_sold()
        available = ticket.qty_available()
        percentage_sold = (sold / ticket.quantity * 100) if ticket.quantity > 0 else 0
        revenue = sold * ticket.price

        ticket_data.append({
            'ticket': ticket,
            'sold': sold,
            'available': available,
            'percentage_sold': round(percentage_sold, 1),
            'revenue': revenue
        })

    context = {
        'tickets': tickets,
        'ticket_data': ticket_data,
        'event_id': event_id,
        'event': event,
        'total_tickets': total_tickets,
        'total_sold': total_sold,
        'total_available': total_available,
        'total_revenue': total_revenue,
        'overall_percentage': round((total_sold / total_tickets * 100) if total_tickets > 0 else 0, 1)
    }

    return render(request, 'ticket_type/ticket_type_list.html', context)


@login_required(login_url='/promoter/account/login/')
def ticket_type_create(request, event_id):
    # Get the event object to ensure it exists
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.event = event  # Assign the event directly
            ticket.save()
            # Redirect back to ticket list for this event
            return redirect('ticket_type_list_per_event', event_id=event_id)
    else:
        # For GET requests, create a simple form without event_id parameter
        form = TicketForm()

    return render(request, 'ticket_type/ticket_type_create.html', {
        'form': form, 
        'event': event,
        'event_id': event_id
    })


@login_required(login_url='/promoter/account/login/')
def ticket_type_update(request, ticket_id):
    instance = get_object_or_404(Ticket, id=ticket_id)

    if request.method == 'POST':
        form = TicketUpdateForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('ticket_type_list_per_event', event_id=instance.event_id)
    else:
        form = TicketUpdateForm(instance=instance)

    return render(request, 'ticket_type/ticket_type_create.html', {
        'form': form, 
        'event': instance.event,
        'event_id': instance.event_id
    })
