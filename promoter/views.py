from django.contrib import messages
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from customer.forms import SignUpFormPromoter, SignInPromoterForm
from event.forms import PromoterForm, ResetPasswordForm, VendorForm
from event.models import Promoter, Event
from promoter.models import Vendor, SalesByVendor


@login_required(login_url='/promoter/account/login/')
def update_promoter(request):
    user_id = request.user.id
    promoter = Promoter.objects.get(user_id=user_id)
    form = PromoterForm(instance=promoter)

    if request.method == 'POST':
        form = PromoterForm(request.POST, instance=promoter)

        if form.is_valid():
            form.save()
            return redirect('events_promoter')
        else:
            return render(request, 'update_promoter.html', {'form': form})
    elif request.method == 'GET':
        return render(request, 'update_promoter.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def reset_password(request):
    if request.method == 'POST':
        form = ResetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')

            return redirect('events_promoter')

        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = ResetPasswordForm(request.user)
    return render(request, 'reset_password.html', {
        'form': form
    })


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
    return render(request, 'promoter/signup_promoter_new.html', {'form': form})


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
    return render(request, 'promoter/signin_promoter_new.html', {'form': form})


def signout_view_promoter(request):
    logout(request)
    return redirect('signin_promoter')


@login_required(login_url='/promoter/account/login/')
def vendors_list(request):
    vendors = Vendor.objects.filter(promoter=request.user.promoter.id)
    return render(request, 'vendor/vendors_list.html', {'vendors': vendors})


@login_required(login_url='/promoter/account/login/')
def vendor_create(request):
    if request.method == 'POST':
        form_vendor = VendorForm(data=request.POST)
        if form_vendor.is_valid():
            vendor = Vendor(**form_vendor.cleaned_data)
            vendor.promoter = request.user.promoter
            vendor.save()
            return redirect('vendors_list')
    else:
        form_vendor = VendorForm()
    return render(request, 'vendor/vendor_create.html', {'form_vendor': form_vendor})


@login_required(login_url='/promoter/account/login/')
def vendor_update(request, vendor_id):
    form_vendor = None
    vendors = Vendor.objects.get(id=vendor_id)
    if request.method == 'GET':
        form_vendor = VendorForm(instance=vendors)
        form_vendor.fields['first_name'].widget.attrs['disabled'] = 'disabled'
        form_vendor.fields['last_name'].widget.attrs['disabled'] = 'disabled'
    if request.method == 'POST':
        form_vendor = VendorForm(request.POST, instance=vendors)
        if form_vendor.is_valid():
            form_vendor.save()
            return redirect('vendors_list')
    return render(request, 'vendor/vendor_create.html', {'form_vendor': form_vendor, 'vendors': vendors})


@login_required(login_url='/promoter/account/login/')
def vendor_remove(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.delete()
    return redirect('vendors_list')


@login_required(login_url='/promoter/account/login/')
def vendor_create_per_event(request, event_id):
    if request.method == 'POST':
        event = Event.objects.get(id=event_id)
        form_vendor = VendorForm(data=request.POST)
        if form_vendor.is_valid():
            vendor = Vendor(**form_vendor.cleaned_data)
            vendor.promoter = request.user.promoter
            vendor.save()
            vendor.event_set.add(event)
            return redirect('update_event', event_id=event_id)
    else:
        form_vendor = VendorForm()
    return render(request, 'vendor/vendor_create.html', {'form_vendor': form_vendor})


@login_required(login_url='/promoter/account/login/')
def vendor_update_per_event(request, event_id):
    vendor = None
    event = Event.objects.get(id=event_id)
    if request.method == "POST":
        vendor_id = request.POST.get('vendors_choice')
        vendor = Vendor.objects.get(id=vendor_id)
        vendor.event_set.add(event)
        return redirect('update_event', event_id=event_id)
    form_vendor = VendorForm()
    return render(request, 'vendor/vendor_create.html', {'form_vendor': form_vendor, 'vendor_select': vendor})


@login_required(login_url='/promoter/account/login/')
def vendors_reports(request):
    tickets = None
    selected_event = None

    if request.method == "POST":
        event_id = request.POST.get('events_choice')
        if event_id:
            tickets = SalesByVendor.objects.filter(event=event_id)
    events = Event.objects.filter(promoter=request.user.promoter).order_by('-created')
    return render(request, 'vendor/vendors_reports.html', {
        'tickets': tickets,
        'events': events,
        'selected_event': selected_event
        })
