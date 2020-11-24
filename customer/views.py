from django.shortcuts import render, redirect
from .forms import SignUpForm, SignInForm
# from django.contrib.auth.models import User
import logging

from django.contrib.auth import login, authenticate, logout

logger = logging.getLogger(__name__)


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
    return render(request, 'accounts/signup.html', {'form': form})


def signin_view(request):
    if request.method == 'POST':
        form = SignInForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('shop:index')
            else:
                return redirect('signup')
    else:
        form = SignInForm()
    return render(request, 'accounts/signin.html', {'form': form})


def signout_view(request):
    logout(request)
    return redirect('signin')
