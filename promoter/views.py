from datetime import datetime
import json
import stripe
from django.contrib import messages
from os import path
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.shortcuts import render, redirect, get_object_or_404
import xlsxwriter
from django.http import StreamingHttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from customer.forms import SignUpFormPromoter, SignInPromoterForm
from event.forms import PromoterForm, ResetPasswordForm, VendorForm
from event.models import Promoter, Event
from local_settings import ENDPOINT_WEBHOOK_PAYOUT
from promoter.models import Vendor, SalesByVendor, BankAccount

from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors


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
def balance_history_payout(request):
    promoter = request.user.promoter
    payouts_history = None
    balance = None
    bank_information = None
    if promoter.account_id:
        payouts_history = stripe.Payout.list(stripe_account=promoter.account_id)

        balance = stripe.Balance.retrieve(
            stripe_account=promoter.account_id
        )

        bank_information = stripe.Account.retrieve(promoter.account_id)

    return render(request, 'payout_list.html', {'promoter': promoter,
                                                'balance': balance,
                                                'payouts_history': payouts_history,
                                                'bank_information': bank_information,
                                                'cents': 100
                                                })


@login_required(login_url='/promoter/account/login/')
def payout_account_link(request):
    promoter = request.user.promoter
    host = request.get_raw_uri().replace(request.get_full_path(), "")
    if not promoter.account_id:
        account_object = stripe.Account.create(
            type="express",
            country="US",
            email=promoter.email,
            capabilities={
                "card_payments": {"requested": True},
                "transfers": {"requested": True},
            },
            business_profile={
                "mcc": "7922",
                "name": promoter.email,
            },
            business_type="individual",
            settings={
                "payouts": {
                    "schedule": {"delay_days": 2, "interval": "weekly", "weekly_anchor": "tuesday"}
                },
            },
        )
        promoter = request.user.promoter
        promoter.account_id = account_object.id
        promoter.save()

    link = stripe.AccountLink.create(
        account=promoter.account_id,
        refresh_url=host + "/promoter/events/",
        return_url=host + "/promoter/events/",
        type="account_onboarding",
    )
    link_connect = link.url

    return render(request, 'payout.html', {'promoter': promoter, 'link_connect': link_connect})


@csrf_exempt
def bank_account_webhook(request):
    endpoint_secret = 'whsec_IrkxuvRttsVB8JmebkRTym5z407dqT9s'
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret, 86400
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    if event['type'] == 'account.external_account.created':
        external_account = event['data']['object']
        print(external_account, "c1")
        promoter_user = Promoter.objects.get(account_id=external_account['account'])
        bank_account = BankAccount.objects.create(
            promoter=promoter_user,
            id_bank_account=external_account['id'],
            last4=external_account['last4'],
            bank_name=external_account['bank_name'],
            routing_number=external_account['routing_number']
        )
        bank_account.save()
    elif event['type'] == 'account.external_account.deleted':
        external_account = event['data']['object']
        bank_account = BankAccount.objects.get(id_bank_account=external_account['id']).delete()
        bank_account.save()
    elif event['type'] == 'account.external_account.updated':
        external_account = event['data']['object']
        try:
            bank_account = BankAccount.objects.get(id_bank_account=external_account['id'])
        except BankAccount.DoesNotExist:
            promoter_user = Promoter.objects.get(account_id=external_account['account'])
            bank_account = BankAccount.objects.create(
                promoter=promoter_user,
                id_bank_account=external_account['id'],
                last4=external_account['last4'],
                bank_name=external_account['bank_name'],
                routing_number=external_account['routing_number']
            )
            bank_account.save()
    else:
        print('Unhandled event type {}'.format(event['type']))
    return HttpResponse(status=200)


@login_required(login_url='/promoter/account/login/')
def bank_account_list(request):
    bank_accounts = None
    link_connect = None
    host = request.get_raw_uri().replace(request.get_full_path(), "")
    promoter = request.user.promoter
    if promoter.account_id:
        bank_accounts = stripe.Account.list_external_accounts(
            promoter.account_id,
            object="bank_account",
            limit=1,
        )
        link = stripe.AccountLink.create(
            account=promoter.account_id,
            refresh_url=host + "/promoter/events/",
            return_url=host + "/promoter/events/",
            type="account_onboarding",
        )
        link_connect = link.url
    return render(request, 'bank_account.html',
                  {'promoter': promoter,
                   'bank_accounts': bank_accounts['data'],
                   'link_connect': link_connect})


def payout_pdf_view(request):
    promoter = request.user.promoter
    width, height = letter
    margin = inch
    mwidth = width - 2 * margin
    mheight = height - 2 * margin

    response = HttpResponse(content_type='application/pdf')
    filename = 'history.pdf'
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    buffer = BytesIO()

    img_file = 'static/img/Eventlinez.png'
    p = canvas.Canvas(buffer)

    p.drawImage(img_file, 230, 790, width=100, preserveAspectRatio=True, mask='auto')
    p.setFont("Helvetica", 16)
    p.setTitle("History payout")
    p.drawString(230, 750, "History payout")
    p.setPageCompression(0)
    # p.translate(0, mheight - inch)
    p.setFont("Helvetica", 20)

    header_collumns = ['Payment Data', 'Amount Paid', 'Status']
    history = stripe.Payout.list(stripe_account=promoter.account_id)
    data = []
    data.append(header_collumns)

    p.translate(margin - 50, margin + 620 - (15 * len(history)))

    for i in history['data']:
        rt = [datetime.fromtimestamp(i.created).strftime("%Y-%m-%d"),
              i.amount / 100, i.status]
        data.append(rt)

    table = Table(data, colWidths=(185, 185, 185))
    table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.gray),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.gray), ]))

    table_style = []

    for i, row in enumerate(data):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i),
                                colors.Color(red=(243.0 / 255), green=(243.0 / 255), blue=(243.0 / 255))))
        else:
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
        if i == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i),
                                colors.Color(red=(60.0 / 255), green=(33.0 / 255), blue=(92.0 / 255))))
            table_style.append(('TEXTCOLOR', (0, i), (-1, i),
                                colors.white))

    table.setStyle(TableStyle(table_style))

    table.wrapOn(p, mwidth, mheight)
    table.drawOn(p, 0, 0)
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response


@csrf_exempt
def webhook_payout(request):
    endpoint_secret = ENDPOINT_WEBHOOK_PAYOUT
    event = None
    payload = request.body
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    payout = None
    subject = None
    message = None
    if event['type'] == 'payout.canceled' or event['type'] == 'payout.failed':
        payout = event['data']['object']

        subject = "Eventlinez - Error Payout"
        message = render_to_string('payout/email_payout.html', {'payout': payout})

    elif event['type'] == 'payout.paid':
        payout = event['data']['object']

        subject = "Eventlinez - New Payout"
        message = render_to_string('payout/email_payout.html', {'payout': payout})

    else:
        print('Unhandled event type {}'.format(event['type']))

    email_payout = EmailMessage(
        subject=subject,
        body=message,
        from_email="noreply@eventlinez.com",
        to=['brunojndias@gmail.com'],
    )
    payout.content_subtype = "html"

    email_payout.send()

    return HttpResponse(status=200)
