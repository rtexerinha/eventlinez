from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
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
        return render(request, 'orders_promoter.html', {'order_details': orders})


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
        form = NewEvent(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            slug = name
            description = form.cleaned_data['description']
            unit_price = form.cleaned_data['unit_price']
            stock = form.cleaned_data['stock']
            available = form.cleaned_data['available']
            category = form.cleaned_data['category']
            image = form.cleaned_data['image']

            events = Event.objects.create(
                name=name,
                slug=slug,
                description=description,
                unit_price=unit_price,
                stock=stock,
                available=available,
                category=category,
                image=image,
                promoter=promoter
            )
            events.save()
            print(events)
            return redirect('events_promoter')
    else:
        form = NewEvent()
    return render(request, 'new_event.html', {'form': form})


def remove_event(request, event_id):
    promoter = request.user.promoter.id
    # event = get_object_or_404(Event, id=event_id)
    event = Event.objects.get(id=event_id, promoter=promoter)
    event.delete()
    return redirect('cart:cart_detail')
