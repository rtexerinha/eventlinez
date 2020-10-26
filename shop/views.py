from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from event.models import Category, Event
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.contrib.auth.models import Group, User
from .forms import SignUpForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout


def index(request, c_slug=None):
    c_page = None
    if c_slug is not None:
        c_page = get_object_or_404(Category, slug=c_slug)
        products_list = Event.objects.filter(category=c_page, available=True)
    else:
        products_list = Event.objects.all().filter(available=True)
    paginator = Paginator(products_list, 3)
    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1
    try:
        events = paginator.page(page)
    except (EmptyPage, InvalidPage):
        events = paginator.page(paginator.num_pages)
    return render(request, 'shop/home.html', {'category': c_page, 'events': events})


def product_event_detail(request, c_slug, event_slug):
    try:
        event = Event.objects.get(category__slug=c_slug, slug=event_slug)
    except Exception as e:
        raise e
    return render(request, 'shop/event.html', {'event': event})


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def signin_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
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
        form = AuthenticationForm()
    return render(request, 'accounts/signin.html', {'form': form})


def signout_view(request):
    logout(request)
    return redirect('signin')
