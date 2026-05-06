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
    import logging

    logger = logging.getLogger(__name__)
    
    try:
        promoter = request.user.promoter.id
        now = timezone.now()
        
        # Optimize queries with select_related and prefetch_related
        events_list = Event.objects.filter(promoter=promoter).select_related('city').prefetch_related('tickets').order_by('-created')

        # Separate active and past events with optimized queries
        active_events = events_list.filter(event_date__gte=now)
        past_events = events_list.filter(event_date__lt=now)

        # Calculate dashboard stats efficiently
        total_events = events_list.count()
        total_active = active_events.count()
        total_past = past_events.count()

        # Optimize revenue and ticket calculations with error handling
        try:
            total_revenue = sum(event.get_amount() for event in events_list)
        except Exception as e:
            logger.error(f"Error calculating total revenue: {e}")
            total_revenue = 0
            
        try:
            total_tickets_sold = sum(event.qty_sould() for event in events_list)
        except Exception as e:
            logger.error(f"Error calculating total tickets sold: {e}")
            total_tickets_sold = 0
            
        try:
            total_tickets_available = sum(event.quantity() for event in events_list)
        except Exception as e:
            logger.error(f"Error calculating total tickets available: {e}")
            total_tickets_available = 0

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
        
    except AttributeError as e:
        logger.error(f"User does not have promoter profile: {e}")
        from django.contrib import messages
        messages.error(request, "You need to have a promoter profile to access this page.")
        return redirect('promoter:signup_promoter')
        
    except Exception as e:
        logger.error(f"Error in event_list view: {e}")
        from django.contrib import messages
        messages.error(request, "An error occurred while loading your events.")
        return render(request, 'event/events_list.html', {
            'events': [],
            'events_count': 0,
            'active_events_count': 0,
            'past_events_count': 0,
            'total_revenue': 0,
            'total_tickets_sold': 0,
            'total_tickets_available': 0,
            'active_events': [],
        })


@login_required(login_url='/promoter/account/login/')
def event_create(request):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            from django.contrib import messages
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
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
        
    except Exception as e:
        logger.error(f"Unexpected error in event_create: {e}")
        from django.contrib import messages
        messages.error(request, "An error occurred while creating the event.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def event_update(request, event_id):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            from django.contrib import messages
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
        
        # Get the event and verify ownership
        event = get_object_or_404(Event, id=event_id, promoter=request.user.promoter)
        
        form = None
        form_vendor = None
        
        # Get related data with error handling
        try:
            vendors = Vendor.objects.filter(promoter=request.user.promoter.id, event=event_id)
            vendors_without_event = Vendor.objects.filter(promoter=request.user.promoter.id).exclude(event=event_id)
            tickets = Ticket.objects.filter(event=event_id)
        except Exception as e:
            logger.error(f"Error fetching related data for event {event_id}: {e}")
            vendors = []
            vendors_without_event = []
            tickets = []
        
        if request.method == 'GET':
            try:
                form = EventForm(instance=event)
                form_vendor = VendorForm()
            except Exception as e:
                logger.error(f"Error creating forms for event {event_id}: {e}")
                from django.contrib import messages
                messages.error(request, "Error loading event form.")
                return redirect('promoter:events_promoter')
                
        if request.method == 'POST':
            try:
                form = EventForm(request.POST, request.FILES, instance=event)
                if form.is_valid():
                    form.save()
                    from django.contrib import messages
                    messages.success(request, "Event updated successfully!")
                    return redirect('promoter:events_promoter')
                else:
                    logger.error(f"Form validation errors for event {event_id}: {form.errors}")
            except Exception as e:
                logger.error(f"Error processing POST for event {event_id}: {e}")
                from django.contrib import messages
                messages.error(request, f"Error updating event: {str(e)}")
                return redirect('promoter:events_promoter')
        
        return render(request, 'event/event_edit_simple.html', {
            'form': form, 
            'tickets': tickets,
            'vendors': vendors,
            'event': event,
            'form_vendor': form_vendor,
            'vendors_without_event': vendors_without_event
        })
        
    except Event.DoesNotExist:
        logger.error(f"Event {event_id} not found or not owned by user {request.user.username}")
        from django.contrib import messages
        messages.error(request, "Event not found or you don't have permission to edit it.")
        return redirect('promoter:events_promoter')
        
    except Exception as e:
        logger.error(f"Unexpected error in event_update for event {event_id}: {e}")
        from django.contrib import messages
        messages.error(request, "An unexpected error occurred while loading the event.")
        return redirect('promoter:events_promoter')


@login_required(login_url='/promoter/account/login/')
def event_remove(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('promoter:events_promoter')


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
    import logging
    from event.models import FullPassEvent
    logger = logging.getLogger(__name__)

    try:
        promoter = request.user.promoter
        event = get_object_or_404(Event, id=event_id)
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        return render(request, 'ticket_type/ticket_type_create.html', {
            'error': f'Event not found: {e}',
            'event_id': event_id
        })

    if request.method == 'POST':
        try:
            form = TicketForm(request.POST, event_id=event_id, promoter=promoter)
            if form.is_valid():
                try:
                    ticket = form.save(commit=False)
                    ticket.event = event
                    ticket.save()

                    # Save full-pass event assignments
                    days = ticket.days or 1
                    if days > 1:
                        FullPassEvent.objects.filter(ticket=ticket).delete()
                        for day in range(1, days + 1):
                            day_event = form.cleaned_data.get(f'full_pass_event_day_{day}')
                            if day_event:
                                FullPassEvent.objects.create(
                                    ticket=ticket,
                                    event=day_event,
                                    day_number=day
                                )

                    logger.info(f"Ticket created successfully for event {event_id}")
                    return redirect('promoter:ticket_type_list_per_event', event_id=event_id)
                except Exception as save_error:
                    logger.error(f"Error saving ticket: {save_error}")
                    form.add_error(None, f"Error saving ticket: {save_error}")
            else:
                logger.error(f"Form validation failed: {form.errors}")
        except Exception as form_error:
            logger.error(f"Error constructing ticket form: {form_error}")
            form = TicketForm(event_id=event_id, promoter=promoter)
            form.add_error(None, f"Error processing form: {form_error}")
    else:
        form = TicketForm(event_id=event_id, promoter=promoter)

    # Pass all promoter events for the JS-driven dynamic dropdowns
    all_promoter_events = Event.objects.filter(promoter=promoter).order_by('-event_date')

    return render(request, 'ticket_type/ticket_type_create.html', {
        'form': form,
        'event': event,
        'event_id': event_id,
        'all_promoter_events': all_promoter_events,
    })


@login_required(login_url='/promoter/account/login/')
def ticket_type_update(request, ticket_id):
    import logging
    from event.models import FullPassEvent
    logger = logging.getLogger(__name__)

    try:
        promoter = request.user.promoter
        instance = get_object_or_404(Ticket, id=ticket_id)
    except Exception as e:
        logger.error(f"Error retrieving ticket {ticket_id}: {e}")
        return render(request, 'ticket_type/ticket_type_create.html', {
            'error': f'Ticket not found: {e}',
            'ticket_id': ticket_id
        })

    if request.method == 'POST':
        try:
            form = TicketUpdateForm(request.POST, instance=instance, promoter=promoter)
            if form.is_valid():
                try:
                    ticket = form.save()

                    # Save full-pass event assignments
                    days = ticket.days or 1
                    if days > 1:
                        FullPassEvent.objects.filter(ticket=ticket).delete()
                        fp_map = {}
                        for day in range(1, days + 1):
                            day_event = form.cleaned_data.get(f'full_pass_event_day_{day}')
                            if day_event:
                                FullPassEvent.objects.create(
                                    ticket=ticket,
                                    event=day_event,
                                    day_number=day
                                )
                                fp_map[day] = day_event

                        # Backfill day_event on already-purchased tickets that have no assignment yet
                        if fp_map:
                            from ticket.models import Ticket as PurchasedTicket
                            for purchased in PurchasedTicket.objects.filter(
                                event_ticket=ticket, day_event__isnull=True, day_number__isnull=False
                            ):
                                if purchased.day_number in fp_map:
                                    purchased.day_event = fp_map[purchased.day_number]
                                    purchased.save(update_fields=['day_event'])

                    logger.info(f"Ticket {ticket_id} updated successfully")
                    return redirect('promoter:ticket_type_list_per_event', event_id=instance.event_id)
                except Exception as save_error:
                    logger.error(f"Error saving ticket: {save_error}")
                    form.add_error(None, f"Error saving ticket: {save_error}")
            else:
                logger.error(f"Validation failed: {form.errors}")
        except Exception as form_error:
            logger.error(f"Error building update form: {form_error}")
            form = TicketUpdateForm(instance=instance, promoter=promoter)
            form.add_error(None, f"Error processing form: {form_error}")
    else:
        form = TicketUpdateForm(instance=instance, promoter=promoter)

    all_promoter_events = Event.objects.filter(promoter=promoter).order_by('-event_date')

    return render(request, 'ticket_type/ticket_type_create.html', {
        'form': form,
        'event': instance.event,
        'event_id': instance.event_id,
        'all_promoter_events': all_promoter_events,
    })