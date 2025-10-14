import logging
from django.contrib import messages
from os import path
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
import xlsxwriter
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta

from customer.forms import SignUpFormPromoter, SignInPromoterForm
from event.forms import PromoterForm, ResetPasswordForm, VendorForm
from event.models import Promoter, Event
from promoter.forms import BankAccountForm, PromoCodeForm
from promoter.models import Payment, Vendor, SalesByVendor, BankAccount, get_balance, PromoCode

from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

logger = logging.getLogger(__name__)


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
            return redirect('payment_list')

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
                return redirect('promoter:promoter_dashboard')  # Use namespaced URL
            else:
                return redirect('promoter:signup_promoter')
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
def payment_list(request):
    promoter = request.user.promoter
    bank_accounts = None
    account_bank_information = None
    form_bank_account = None
    account_number_mask = None
    payouts_history = Payment.objects.filter(promoter=promoter)
    balance = get_balance(request.user.promoter)
    bank_information = BankAccount.objects.filter(promoter=promoter)
    if bank_information:
        bank_accounts = BankAccount.objects.get(id=bank_information[0].id)
        account_number_mask = bank_accounts.account_number[-4:].rjust(len(bank_accounts.account_number), "*")
    if request.method == 'GET':
        form_bank_account = BankAccountForm(instance=bank_accounts)
    data = {'promoter': promoter, 'balance': balance, 'payouts_history': payouts_history,
            'form': form_bank_account, 'bank_information': bank_accounts,
            'account_number_mask': account_number_mask
            }
    return render(request, 'payments/payment_list.html', data)


def payment_pdf_view(request):
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
    historys = Payment.objects.filter(promoter=promoter)
    data = []
    data.append(header_collumns)

    p.translate(margin - 50, margin + 620 - (15 * len(historys)))

    for i in historys:
        history = [i.created.strftime("%Y-%m-%d"), i.amount, 'Paid']
        data.append(history)

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


def bank_create(request):
    if request.method == 'POST':
        form = BankAccountForm(data=request.POST)
        if form.is_valid():
            bank_account = BankAccount(**form.cleaned_data)
            bank_account.promoter = request.user.promoter
            bank_account.save()
            return redirect('payment_list')
    else:
        form = BankAccountForm()
    return render(request, 'bank/bank_account_create.html', {'form': form})


@login_required(login_url='/promoter/account/login/')
def bank_account_list(request):
    bank_accounts = None
    form_bank_account = None
    account_bank_information = None
    account_number_mask = None
    bank_information = BankAccount.objects.filter(promoter=request.user.promoter)
    if bank_information:
        bank_accounts = BankAccount.objects.get(id=bank_information[0].id)
        account_number_mask = bank_accounts.account_number[-4:].rjust(len(bank_accounts.account_number), "*")
    if request.method == 'GET':
        form_bank_account = BankAccountForm(instance=bank_accounts)

    data = {'promoter': request.user.promoter,
            'form': form_bank_account, 
            'account_number_mask': account_number_mask,
            'bank_information': bank_accounts}
    return render(request, 'bank/bank_account.html', data)


@login_required(login_url='/promoter/account/login/')
def bank_account_update(request, bank_id):
    form_bank_account = None
    bank_accounts = BankAccount.objects.get(id=bank_id)
    if request.method == 'GET':
        form_bank_account = BankAccountForm(instance=bank_accounts)
    if request.method == 'POST':
        form_bank_account = BankAccountForm(request.POST, instance=bank_accounts)
        if form_bank_account.is_valid():
            form_bank_account.save()
            return redirect('payment_list')
    return render(request, 'bank/bank_account_create.html',
                  {'form': form_bank_account})


@login_required(login_url='/promoter/account/login/')
def bank_remove(request, bank_id):
    bank = get_object_or_404(BankAccount, id=bank_id)
    bank.delete()
    return redirect('bank_information')


# Promo Code Management Views
@login_required(login_url='/promoter/account/login/')
def promo_codes_list(request):
    """List all promo codes for the current promoter"""
    promoter = request.user.promoter
    promo_codes = PromoCode.objects.filter(promoter=promoter).order_by('-created_at')
    
    return render(request, 'promo_codes/promo_codes_list.html', {
        'promo_codes': promo_codes,
        'promoter': promoter
    })


@login_required(login_url='/promoter/account/login/')
def promo_code_create(request):
    """Create a new promo code"""
    promoter = request.user.promoter
    
    if request.method == 'POST':
        form = PromoCodeForm(request.POST, promoter=promoter)
        if form.is_valid():
            promo_code = form.save(commit=False)
            promo_code.promoter = promoter
            promo_code.save()
            messages.success(request, f'Promo code "{promo_code.code}" created successfully!')
            return redirect('promo_codes_list')
    else:
        form = PromoCodeForm(promoter=promoter)
    
    return render(request, 'promo_codes/promo_code_create.html', {
        'form': form,
        'promoter': promoter
    })


@login_required(login_url='/promoter/account/login/')
def promo_code_update(request, promo_code_id):
    """Update an existing promo code"""
    promoter = request.user.promoter
    promo_code = get_object_or_404(PromoCode, id=promo_code_id, promoter=promoter)
    
    if request.method == 'POST':
        form = PromoCodeForm(request.POST, instance=promo_code, promoter=promoter)
        if form.is_valid():
            form.save()
            messages.success(request, f'Promo code "{promo_code.code}" updated successfully!')
            return redirect('promo_codes_list')
    else:
        form = PromoCodeForm(instance=promo_code, promoter=promoter)
    
    return render(request, 'promo_codes/promo_code_update.html', {
        'form': form,
        'promo_code': promo_code,
        'promoter': promoter
    })


@login_required(login_url='/promoter/account/login/')
def promo_code_delete(request, promo_code_id):
    """Delete a promo code"""
    promoter = request.user.promoter
    promo_code = get_object_or_404(PromoCode, id=promo_code_id, promoter=promoter)
    
    if request.method == 'POST':
        code_name = promo_code.code
        promo_code.delete()
        messages.success(request, f'Promo code "{code_name}" deleted successfully!')
        return redirect('promo_codes_list')
    
    return render(request, 'promo_codes/promo_code_delete.html', {
        'promo_code': promo_code,
        'promoter': promoter
    })


@login_required(login_url='/promoter/account/login/')
def promo_code_toggle_status(request, promo_code_id):
    """Toggle promo code active status"""
    promoter = request.user.promoter
    promo_code = get_object_or_404(PromoCode, id=promo_code_id, promoter=promoter)
    
    promo_code.is_active = not promo_code.is_active
    promo_code.save()
    
    status = "activated" if promo_code.is_active else "deactivated"
    messages.success(request, f'Promo code "{promo_code.code}" {status} successfully!')
    
    return redirect('promo_codes_list')


@login_required(login_url='/promoter/account/login/')
def promoter_dashboard(request):
    """
    Comprehensive promoter dashboard with business overview and quick actions
    """
    promoter = request.user.promoter
    now = timezone.now()
    
    # Get events with optimized queries
    all_events = Event.objects.filter(promoter=promoter).select_related('city').prefetch_related('tickets')
    active_events = all_events.filter(event_date__gte=now).order_by('event_date')
    past_events = all_events.filter(event_date__lt=now).order_by('-event_date')
    
    # Dashboard metrics
    total_events = all_events.count()
    active_events_count = active_events.count()
    past_events_count = past_events.count()
    
    # Revenue calculations
    total_revenue = sum(event.get_amount() for event in all_events)
    monthly_revenue = sum(event.get_amount() for event in all_events.filter(
        created__gte=now - timedelta(days=30)
    ))
    
    # Ticket statistics
    total_tickets_sold = sum(event.qty_sould() for event in all_events)
    total_tickets_available = sum(event.quantity() for event in all_events)
    tickets_sold_percentage = (total_tickets_sold / total_tickets_available * 100) if total_tickets_available > 0 else 0
    
    # Recent activities
    recent_events = all_events.order_by('-created')[:5]
    upcoming_events = active_events[:3]
    
    # Performance data for charts
    last_6_months = []
    monthly_stats = []
    
    for i in range(6):
        month_start = now.replace(day=1) - timedelta(days=i*30)
        month_end = month_start + timedelta(days=30)
        
        month_events = all_events.filter(
            created__gte=month_start,
            created__lt=month_end
        )
        
        month_revenue = sum(event.get_amount() for event in month_events)
        month_tickets = sum(event.qty_sould() for event in month_events)
        
        last_6_months.insert(0, {
            'month': month_start.strftime('%b %Y'),
            'revenue': month_revenue,
            'tickets': month_tickets,
            'events': month_events.count()
        })
    
    # Payment and balance info
    current_balance = get_balance(promoter)
    recent_payments = Payment.objects.filter(promoter=promoter).order_by('-created')[:5]
    
    # Bank account status
    has_bank_account = BankAccount.objects.filter(promoter=promoter).exists()
    
    # Promo codes summary
    active_promo_codes = PromoCode.objects.filter(
        promoter=promoter, 
        is_active=True,
        valid_until__gte=now
    ).count()
    
    # Top performing events
    top_events = all_events.annotate(
        revenue=Sum('tickets__price')
    ).order_by('-revenue')[:3]
    
    context = {
        'promoter': promoter,
        'dashboard_data': {
            'total_events': total_events,
            'active_events_count': active_events_count,
            'past_events_count': past_events_count,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'total_tickets_sold': total_tickets_sold,
            'total_tickets_available': total_tickets_available,
            'tickets_sold_percentage': round(tickets_sold_percentage, 1),
            'current_balance': current_balance,
            'has_bank_account': has_bank_account,
            'active_promo_codes': active_promo_codes,
        },
        'recent_events': recent_events,
        'upcoming_events': upcoming_events,
        'recent_payments': recent_payments,
        'top_events': top_events,
        'monthly_stats': last_6_months,
        'quick_actions': [
            {
                'title': 'Create New Event',
                'url': 'new_events',
                'icon': 'fas fa-plus-circle',
                'color': 'primary',
                'description': 'Set up a new event and start selling tickets'
            },
            {
                'title': 'Manage Events',
                'url': 'events_promoter',
                'icon': 'fas fa-calendar-alt',
                'color': 'info',
                'description': 'View and edit your existing events'
            },
            {
                'title': 'View Payments',
                'url': 'payment_list',
                'icon': 'fas fa-credit-card',
                'color': 'success',
                'description': 'Check your payment history and balance'
            },
            {
                'title': 'Promo Codes',
                'url': 'promo_codes_list',
                'icon': 'fas fa-tags',
                'color': 'warning',
                'description': 'Create and manage discount codes'
            },
        ]
    }
    
    return render(request, 'promoter/dashboard.html', context)
