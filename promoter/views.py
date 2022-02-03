import stripe
from django.contrib import messages
from io import BytesIO
from os import path
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
import xlsxwriter
from django.http import StreamingHttpResponse

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
            address = form.cleaned_data.get('address')
            city = form.cleaned_data.get('city')
            zips = form.cleaned_data.get('zip')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            stripe.api_key = "sk_test_YHj724JNB8fMwCfcCb4ieHRU007hQB7qwU"
            account_object = stripe.Account.create(
                type="express",
                country="US",
                email=username,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                business_profile={
                    "mcc": "7922",
                    "name": username,
                },
                business_type="individual",
                individual={
                    "address": {
                        "city": city,
                        "country": "US",
                        "line1": address,
                        "postal_code": zips,
                    },
                },
            )
            promoter = request.user.promoter
            promoter.account_id = account_object.id
            promoter.save()
            # return redirect('events_promoter')
            return redirect('payout_stripe')

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
            selected_event = Event.objects.get(id=event_id)
    events = Event.objects.filter(promoter=request.user.promoter).order_by('-created')
    return render(request, 'vendor/vendors_reports.html', {
        'tickets': tickets,
        'events': events,
        'selected_event': selected_event
    })


@login_required(login_url='/promoter/account/login/')
def vendor_export_excel(request, event_id):
    out = BytesIO()
    response = StreamingHttpResponse(
        out, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=sales_by_vendors.xlsx'

    workbook = xlsxwriter.Workbook(out)
    sheet = workbook.add_worksheet("Sales by Vendor")
    sheet.set_tab_color('#3c215c')

    props_float = {'num_format': '[$$-409]#,##0.00', 'font_size': 10, 'align': 'vcenter', 'color': '#171717',
                   'bg_color': '#FFFFFF', 'font_name': 'Arial', 'bottom': 1,
                   'bottom_color': '#dee2e6', 'valign': 'vcenter'}

    title_props = {'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'font_name': 'Arial'}

    props_header = {'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
                    'color': '#171717', 'bg_color': '#F4F4F4', 'font_name': 'Arial'}

    props_table = {'font_size': 10, 'align': 'center', 'color': '#171717', 'bg_color': '#FFFFFF',
                   'font_name': 'Arial', 'bottom': 1, 'bottom_color': '#dee2e6', 'valign': 'vcenter'}

    props_event = {'font_size': 10, 'align': 'left', 'color': '#171717', 'bg_color': '#FFFFFF',
                   'font_name': 'Arial', 'bottom': 1, 'bottom_color': '#dee2e6', 'valign': 'left'}

    title_format = workbook.add_format(title_props)
    tthead = workbook.add_format(props_header)
    event_style = workbook.add_format(props_event)
    tbody_style = workbook.add_format(props_table)
    money_format = workbook.add_format(props_float)

    sheet.set_column('A:A', 40)
    sheet.set_column('B:B', 40)
    sheet.set_column('C:C', 20)
    sheet.set_column('D:D', 20)
    sheet.set_row(1, 25)
    sheet.set_default_row(30)
    sheet.merge_range('A1:F1', u"", title_format)

    tickets = SalesByVendor.objects.filter(event=event_id).values_list(
        'event__name', 'vendor__first_name', 'vendor__last_name', 'qty', 'amount').order_by('-event')

    row_num = 1
    columns = ['event', 'vendor', 'qty', 'amount']
    for col_num in range(len(columns)):
        sheet.write(row_num, col_num, columns[col_num], tthead)

    for idx, data in enumerate(tickets):
        row = 2 + idx
        sheet.write_string(row, 0, data[0], event_style)
        sheet.write_string(row, 1, data[1] + ' ' + data[2], event_style)
        sheet.write_number(row, 2, data[3], tbody_style)
        sheet.write_number(row, 3, data[4], money_format, )

    way = path.abspath("static")
    logo = path.join(way, 'img', 'logo.png')
    sheet.insert_image('A1', logo)

    workbook.close()
    out.seek(0)
    return response


@login_required(login_url='/promoter/account/login/')
def balance_stripe(request):
    promoter = request.user.promoter

    balance = stripe.Balance.retrieve(
        stripe_account=promoter.account_id
    )

    #TODO: Melhorar a forma de conversão dos valores
    available100 = balance.available[0].amount / 100
    instant_available100 = balance.instant_available[0].amount / 100
    pending100 = balance.pending[0].amount / 100

    return render(request, 'balance_payout.html', {'promoter': promoter,
                                                   'balance': balance,
                                                   'available100': available100,
                                                   'instant_available100': instant_available100,
                                                   'pending100': pending100,
                                                   })


@login_required(login_url='/promoter/account/login/')
def payout_history(request):
    promoter = request.user.promoter
    history = stripe.Account.create_login_link(
        promoter.account_id,
    )
    link_history = history.url
    payouts_history = stripe.Payout.list(stripe_account=promoter.account_id)

    return render(request, 'payout_history.html', {'promoter': promoter, 'link_history': link_history,
                                                   'payouts_history': payouts_history})


@login_required(login_url='/promoter/account/login/')
def payout_account_link(request):
    promoter = request.user.promoter
    host = request.get_raw_uri().replace(request.get_full_path(), "")
    if promoter.account_id:
        link = stripe.AccountLink.create(
            account=promoter.account_id,
            refresh_url=host + "/promoter/events/",
            return_url=host + "/promoter/events/",
            type="account_onboarding",
        )
        link_connect = link.url

        bank_information = stripe.Account.retrieve(promoter.account_id)

        return render(request, 'payout_create.html', {'promoter': promoter,
                                                      'bank_information': bank_information,
                                                      'link_connect': link_connect})
    return render(request, 'payout_create.html', {'promoter': promoter, 'link_connect': None})
