from django.shortcuts import render, get_object_or_404

from event.models import Ticket
from .models import Order
from django.contrib.auth.decorators import login_required


@login_required()
def thanks(request, order_id):
    customer_order = None
    tickets = None
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
        tickets = Ticket.objects.filter(order_item__order=customer_order)
    return render(request, 'thanks.html', {'customer_order': customer_order, 'tickets': tickets})


@login_required()
def order_list(request):
    email = str(request.user.username)
    orders = Order.objects.filter(emailAddress=email)
    return render(request, 'order/orders_list.html', {'orders': orders})


@login_required()
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'order/order_detail.html', {'order': order})


