from datetime import datetime, timedelta
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from itertools import chain

from cart.models import Cart, CartItem
from cart.views import _cart_id
from ticket.models import Ticket
from .forms import SignUpForm, SignInForm, CustomerForm, UserForm, \
    ResetPasswordForm
import logging
from .models import Customer
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.conf import settings

logger = logging.getLogger(__name__)


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user_auth = authenticate(username=username, password=password)
            login(request, user_auth)
            if request.COOKIES.get('backpage') is not None:
                pageback = request.COOKIES['backpage']
                return HttpResponseRedirect(pageback)
            return redirect('shop:index')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup_customer_new.html', {'form': form, 'PROD': settings.PROD})


def signin_view(request):
    if request.method == 'POST':
        form = SignInForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            customer = authenticate(username=username, password=password)
            if customer is not None:
                login(request, customer)
                if request.COOKIES.get('backpage') is not None:
                    pageback = request.COOKIES['backpage']
                    return HttpResponseRedirect(pageback)
                return redirect('shop:index')
            else:
                return redirect('signup')
    else:
        form = SignInForm()
    return render(request, 'accounts/signin_customer_new.html', {'form': form, 'PROD': settings.PROD})


def signout_view(request):
    logout(request)
    return redirect('signin')


@login_required
def update_customer(request):
    user_id = request.user.id
    customer = Customer.objects.get(user_id=user_id)
    form = CustomerForm(instance=customer)
    user_form = UserForm(instance=request.user)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        
        if form.is_valid():
            form.save()
            return redirect('customer_update')
        else:
            return render(request, 'accounts/update_customer.html', {'form': form, 'user': user_form, 'PROD': settings.PROD})
    elif request.method == 'GET':
        return render(request, 'accounts/update_customer.html', {'form': form, 'user': user_form, 'PROD': settings.PROD})


@login_required
def change_password_customer(request):

    if request.method == 'POST':
        form = ResetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')

            return redirect('shop:index')

        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ResetPasswordForm(request.user)
    return render(request, 'accounts/change_password_customer.html', {
        'form': form,
        'PROD': settings.PROD
    })


@csrf_exempt
@login_required
def edit_guest(request):
    id = request.POST.get('id', '')
    type = request.POST.get('type', '')
    value = request.POST.get('value', '')
    ticket = Ticket.objects.get(id=id)
    if type == "guest_name":
        ticket.guest_name = value

    ticket.save()
    return JsonResponse({"success": "Updated"})


@login_required()
def guest_list(request):
    enddate = datetime.today() + timedelta(days=-1)
    tickets = Ticket.objects.filter(
        event_ticket__event__event_date__gte=enddate).order_by('-created_at')

    tickets = tickets.filter(Q(customer=request.user.customer) | Q(email=request.user.customer.email))
    return render(request, 'ticket/ticket_customer.html', {'tickets': tickets, 'PROD': settings.PROD})
