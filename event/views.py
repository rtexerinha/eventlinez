import csv

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from event.forms import NewEvent
from event.models import Event
from order.models import Order


def order_promoter(request):
    # TODO: Verifica possibilidade de simplificar código sobre login
    if not request.user.is_authenticated:
        return redirect('signin_promoter')
    else:
        promoter = request.user.promoter
        orders = Order.objects.filter(orderitem__event__promoter=promoter)
        paginator = Paginator(orders, 8)
        page = int(request.GET.get('page', '1'))
        try:
            orders = paginator.page(page)
        except (EmptyPage, InvalidPage):
            orders = paginator.page(paginator.num_pages)
        return render(request, 'orders_promoter.html', {'orders': orders})


@login_required
def events_promoter(request):
    if request.user.is_authenticated:
        promoter = request.user.promoter.id
        events = Event.objects.filter(promoter=promoter)
        return render(request, 'events_promoter.html', {'events': events})
    else:
        return render(request, 'accounts/signin_promoter.html')


def order_per_events(request):
    if not request.user.is_authenticated:
        return render(request, 'accounts/signin_promoter.html')
    else:
        promoter = request.user.promoter.id
        events = Event.objects.filter(promoter=promoter)
        orders = Order.objects.filter(event=events)
        return render(request, 'events_promoter.html', {'order_details': orders})


def new_events(request):
    promoter = request.user.promoter
    if request.method == 'POST':
        form = NewEvent(request.POST, request.FILES)
        if form.is_valid():
            name = form.cleaned_data['name']
            unit_price = form.cleaned_data['unit_price']
            stock = form.cleaned_data['stock']
            category = form.cleaned_data['category']
            description = form.cleaned_data['description']
            event_date = form.cleaned_data['event_date']
            event_address = form.cleaned_data['event_address']
            image = form.cleaned_data['image']
            available = form.cleaned_data['available']

            events = Event.objects.create(
                name=name,
                unit_price=unit_price,
                stock=stock,
                category=category,
                description=description,
                event_date=event_date,
                promoter=promoter,
                event_address=event_address,
                image=image,
                available=available,
            )
            events.save()
            print(events)
            return redirect('events_promoter')
    else:
        form = NewEvent()
    return render(request, 'new_event.html', {'form': form})


def remove_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('events_promoter')


def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order', 'Customer', 'Email', 'Date', 'Total'])

    orders = Order.objects.all().values_list('id', 'billingName', 'emailAddress', 'created', 'total')

    for list_order in orders:
        writer.writerow(list_order)

    return response
