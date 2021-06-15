from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

from event.models import Ticket
from .forms import SignUpForm, SignInForm, SignUpFormPromoter, SignInPromoterForm, CustomerForm, UserForm, \
    ResetPasswordForm
import logging
from .models import Customer
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages

logger = logging.getLogger(__name__)


def signup_view_promoter(request):
    if request.method == 'POST':
        form = SignUpFormPromoter(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('events_promoter')
    else:
        form = SignUpFormPromoter()
    return render(request, 'accounts/signup_promoter.html', {'form': form})


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            user_auth = authenticate(username=username, password=password)
            login(request, user_auth)
            return redirect('shop:index')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup_customer.html', {'form': form})


def signin_view_promoter(request):
    if request.method == 'POST':
        form = SignInPromoterForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            promoter = authenticate(username=username, password=password)
            if promoter is not None:
                login(request, promoter)
                return redirect('events_promoter')
            else:
                return redirect('signup_promoter')
    else:
        form = SignInPromoterForm()
    return render(request, 'accounts/signin_promoter.html', {'form': form})


def signin_view(request):
    if request.method == 'POST':
        form = SignInForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            customer = authenticate(username=username, password=password)
            if customer is not None:
                login(request, customer)
                return redirect('shop:index')
            else:
                return redirect('signup')
    else:
        form = SignInForm()
    return render(request, 'accounts/signin_customer_new.html', {'form': form})


def signout_view_promoter(request):
    logout(request)
    return redirect('signin_promoter')


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
            return redirect('shop:index')
        else:
            return render(request, 'accounts/update_customer.html', {'form': form, 'user': user_form})
    elif request.method == 'GET':
        return render(request, 'accounts/update_customer.html', {'form': form, 'user': user_form})


@login_required
def reset_password_customer(request):

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
    return render(request, 'accounts/reset_password_customer.html', {
        'form': form
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
    today = datetime.today()
    email = str(request.user.customer.id)
    tickets = Ticket.objects.filter(customer=email, event__event_date__gte=today)
    return render(request, 'ticket/ticket_customer.html', {'tickets': tickets})
