from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .forms import SignUpForm, SignInForm, SignUpFormPromoter, SignInPromoterForm, CustomerForm, UserForm, \
    ResetPasswordForm
import logging
from .models import Customer
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib import messages
from django.db import transaction, DatabaseError
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
            email = form.cleaned_data['email']
            username = form.cleaned_data['email']
            password = form.cleaned_data['password1']
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data['last_name']
            cellphone = form.cleaned_data['cellphone']
            address = form.cleaned_data['address']

            try:
                with transaction.atomic():
                    user = User.objects.create_user(email=email, username=username, password=password,
                                                    first_name=first_name)
                    customer = Customer.objects.create(user=user, email=email, first_name=first_name,
                                                       last_name=last_name, cellphone=cellphone, address=address)
                user_auth = authenticate(username=username, password=password)
                login(request, user_auth)
                return redirect('shop:index')
            except DatabaseError:
                pass
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
    return render(request, 'accounts/signin_customer.html', {'form': form})


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
