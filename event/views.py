from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from event.models import Event
from order.models import Order


@login_required
def order_promoter(request):
    if request.user.is_authenticated:
        promoter = request.user.promoter.id
        events = Event.objects.filter(promoter=promoter)
        # promoter_orders = Order.objects.filter(orderitem=events.id)
        return render(request, 'orders_promoter.html')
        # return render(request, 'orders_promoter.html', {'promoter_orders': promoter_orders})
    else:
        return render(request, 'accounts/signin_customer.html')


@login_required
def events_promoter(request):
    if request.user.is_authenticated:
        promoter = request.user.promoter.id
        events = Event.objects.filter(promoter=promoter)
        return render(request, 'events_promoter.html', {'events': events})
    else:
        return render(request, 'accounts/signin_customer.html')
