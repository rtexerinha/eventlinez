from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from event.models import Event
from order.models import Order


def order_promoter(request):
    # TODO: Verifica possibilidade de simplificar código sobre login
    if not request.user.is_authenticated:
        return redirect('signin_promoter')
    else:
        promoter = request.user.promoter
        orders = Order.objects.filter(orderitem__event__promoter=promoter)
        return render(request, 'orders_promoter.html', {'order_details': orders})


@login_required
def events_promoter(request):
    if request.user.is_authenticated:
        promoter = request.user.promoter.id
        events = Event.objects.filter(promoter=promoter)
        return render(request, 'events_promoter.html', {'events': events})
    else:
        return render(request, 'accounts/signin_customer.html')
