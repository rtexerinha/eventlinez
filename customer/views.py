from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import SignUpForm, SignInForm, SignUpFormPromoter, SignInPromoterForm, CustomerForm, UserForm
import logging
from .models import Customer
from django.contrib.auth import login, authenticate, logout

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
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
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
