from django.shortcuts import render, get_object_or_404

from event.models import Ticket
from .models import Order
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def thanks(request, order_id):
    customer_order = None
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thanks.html', {'customer_order': customer_order})


@login_required()
def order_list(request):
    email = str(request.user.username)
    orders = Order.objects.filter(emailAddress=email)
    return render(request, 'order/orders_list.html', {'orders': orders})


@login_required()
def order_detail(request, order_id):
    order = Order.objects.get(id=order_id)
    return render(request, 'order/order_detail.html', {'order': order})


@login_required()
def ticket_list(request):
    email = str(request.user.customer.id)
    tickets = Ticket.objects.filter(customer=email)
    orders = Order.objects.filter(customer=email)
    return render(request, 'ticket/ticket_customer.html', {'tickets': tickets, 'orders': orders})

@csrf_exempt
def saveTicket(request):
    id=request.POST.get('id','')
    type=request.POST.get('type','')
    value=request.POST.get('value','')
    ticket=Ticket.objects.get(id=id)
    if type=="guest_name":
       ticket.guest_name=value

    ticket.save()
    return JsonResponse({"success":"Updated"})
