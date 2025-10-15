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
from promoter.models import Payment, Vendor, SalesByVendor, BankAccount, get_balance, PromoCode, Subscription

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
            return redirect('promoter:events_promoter')
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

            return redirect('promoter:events_promoter')

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
            # return redirect('promoter:events_promoter')
            return redirect('promoter:payment_list')

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
    return redirect('promoter:signin_promoter')


@login_required(login_url='/promoter/account/login/')
def vendors_list(request):
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            from django.contrib import messages
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        vendors = Vendor.objects.filter(promoter=request.user.promoter.id)
        return render(request, 'vendor/vendors_list.html', {'vendors': vendors})
        
    except Exception as e:
        logger.error(f"Unexpected error in vendors_list: {e}")
        from django.contrib import messages
        messages.error(request, "An error occurred while loading vendors.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def vendor_create(request):
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        if request.method == 'POST':
            form_vendor = VendorForm(data=request.POST)
            if form_vendor.is_valid():
                vendor = Vendor(**form_vendor.cleaned_data)
                vendor.promoter = request.user.promoter
                vendor.save()
                return redirect('promoter:vendors_list')
        else:
            form_vendor = VendorForm()
        return render(request, 'vendor/vendor_create.html', {'form_vendor': form_vendor})
        
    except Exception as e:
        logger.error(f"Unexpected error in vendor_create: {e}")
        messages.error(request, "An error occurred while creating the vendor.")
        return redirect('promoter:signup_promoter')


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
            return redirect('promoter:vendors_list')
    return render(request, 'vendor/vendor_create.html', {'form_vendor': form_vendor, 'vendors': vendors})


@login_required(login_url='/promoter/account/login/')
def vendor_remove(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    vendor.delete()
    return redirect('promoter:vendors_list')


@login_required(login_url='/promoter/account/login/')
def vendor_create_per_event(request, event_id):
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        if request.method == 'POST':
            event = Event.objects.get(id=event_id)
            form_vendor = VendorForm(data=request.POST)
            if form_vendor.is_valid():
                vendor = Vendor(**form_vendor.cleaned_data)
                vendor.promoter = request.user.promoter
                vendor.save()
                vendor.event_set.add(event)
                return redirect('promoter:update_event', event_id=event_id)
        else:
            form_vendor = VendorForm()
        return render(request, 'vendor/vendor_create.html', {'form_vendor': form_vendor})
        
    except Exception as e:
        logger.error(f"Unexpected error in vendor_create_per_event: {e}")
        messages.error(request, "An error occurred while creating the vendor.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def vendor_update_per_event(request, event_id):
    vendor = None
    event = Event.objects.get(id=event_id)
    if request.method == "POST":
        vendor_id = request.POST.get('vendors_choice')
        vendor = Vendor.objects.get(id=vendor_id)
        vendor.event_set.add(event)
        return redirect('promoter:update_event', event_id=event_id)
    form_vendor = VendorForm()
    return render(request, 'vendor/vendor_create.html', {'form_vendor': form_vendor, 'vendor_select': vendor})


@login_required(login_url='/promoter/account/login/')
def vendors_reports(request):
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
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
        
    except Exception as e:
        logger.error(f"Unexpected error in vendors_reports: {e}")
        messages.error(request, "An error occurred while loading vendor reports.")
        return redirect('promoter:signup_promoter')


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
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
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
        
    except Exception as e:
        logger.error(f"Unexpected error in payment_list: {e}")
        messages.error(request, "An error occurred while loading payment information.")
        return redirect('promoter:signup_promoter')


def payment_pdf_view(request):
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
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
        
    except Exception as e:
        logger.error(f"Unexpected error in payment_pdf_view: {e}")
        messages.error(request, "An error occurred while generating the PDF.")
        return redirect('promoter:signup_promoter')


def bank_create(request):
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        if request.method == 'POST':
            form = BankAccountForm(data=request.POST)
            if form.is_valid():
                bank_account = BankAccount(**form.cleaned_data)
                bank_account.promoter = request.user.promoter
                bank_account.save()
                return redirect('promoter:payment_list')
        else:
            form = BankAccountForm()
        return render(request, 'bank/bank_account_create.html', {'form': form})
        
    except Exception as e:
        logger.error(f"Unexpected error in bank_create: {e}")
        messages.error(request, "An error occurred while creating the bank account.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def bank_account_list(request):
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
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
        
    except Exception as e:
        logger.error(f"Unexpected error in bank_account_list: {e}")
        messages.error(request, "An error occurred while loading bank account information.")
        return redirect('promoter:signup_promoter')


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
            return redirect('promoter:payment_list')
    return render(request, 'bank/bank_account_create.html',
                  {'form': form_bank_account})


@login_required(login_url='/promoter/account/login/')
def bank_remove(request, bank_id):
    bank = get_object_or_404(BankAccount, id=bank_id)
    bank.delete()
    return redirect('promoter:bank_information')


# Promo Code Management Views
@login_required(login_url='/promoter/account/login/')
def promo_codes_list(request):
    """List all promo codes for the current promoter"""
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        promoter = request.user.promoter
        promo_codes = PromoCode.objects.filter(promoter=promoter).order_by('-created_at')
        
        return render(request, 'promo_codes/promo_codes_list.html', {
            'promo_codes': promo_codes,
            'promoter': promoter
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in promo_codes_list: {e}")
        messages.error(request, "An error occurred while loading promo codes.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def promo_code_create(request):
    """Create a new promo code"""
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        promoter = request.user.promoter
        
        if request.method == 'POST':
            form = PromoCodeForm(request.POST, promoter=promoter)
            if form.is_valid():
                promo_code = form.save(commit=False)
                promo_code.promoter = promoter
                promo_code.save()
                messages.success(request, f'Promo code "{promo_code.code}" created successfully!')
                return redirect('promoter:promo_codes_list')
        else:
            form = PromoCodeForm(promoter=promoter)
        
        return render(request, 'promo_codes/promo_code_create.html', {
            'form': form,
            'promoter': promoter
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in promo_code_create: {e}")
        messages.error(request, "An error occurred while creating the promo code.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def promo_code_update(request, promo_code_id):
    """Update an existing promo code"""
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        promoter = request.user.promoter
        promo_code = get_object_or_404(PromoCode, id=promo_code_id, promoter=promoter)
        
        if request.method == 'POST':
            form = PromoCodeForm(request.POST, instance=promo_code, promoter=promoter)
            if form.is_valid():
                form.save()
                messages.success(request, f'Promo code "{promo_code.code}" updated successfully!')
                return redirect('promoter:promo_codes_list')
        else:
            form = PromoCodeForm(instance=promo_code, promoter=promoter)
        
        return render(request, 'promo_codes/promo_code_update.html', {
            'form': form,
            'promo_code': promo_code,
            'promoter': promoter
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in promo_code_update: {e}")
        messages.error(request, "An error occurred while updating the promo code.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def promo_code_delete(request, promo_code_id):
    """Delete a promo code"""
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        promoter = request.user.promoter
        promo_code = get_object_or_404(PromoCode, id=promo_code_id, promoter=promoter)
        
        if request.method == 'POST':
            code_name = promo_code.code
            promo_code.delete()
            messages.success(request, f'Promo code "{code_name}" deleted successfully!')
            return redirect('promoter:promo_codes_list')
        
        return render(request, 'promo_codes/promo_code_delete.html', {
            'promo_code': promo_code,
            'promoter': promoter
        })
        
    except Exception as e:
        logger.error(f"Unexpected error in promo_code_delete: {e}")
        messages.error(request, "An error occurred while deleting the promo code.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def promo_code_toggle_status(request, promo_code_id):
    """Toggle promo code active status"""
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        promoter = request.user.promoter
        promo_code = get_object_or_404(PromoCode, id=promo_code_id, promoter=promoter)
        
        promo_code.is_active = not promo_code.is_active
        promo_code.save()
        
        status = "activated" if promo_code.is_active else "deactivated"
        messages.success(request, f'Promo code "{promo_code.code}" {status} successfully!')
        
        return redirect('promoter:promo_codes_list')
        
    except Exception as e:
        logger.error(f"Unexpected error in promo_code_toggle_status: {e}")
        messages.error(request, "An error occurred while updating the promo code status.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def promoter_dashboard(request):
    """
    Comprehensive promoter dashboard with business overview and quick actions
    """
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
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
                    'url': 'promoter:new_events',
                    'icon': 'fas fa-plus-circle',
                    'color': 'primary',
                    'description': 'Set up a new event and start selling tickets'
                },
                {
                    'title': 'Manage Events',
                    'url': 'promoter:events_promoter',
                    'icon': 'fas fa-calendar-alt',
                    'color': 'info',
                    'description': 'View and edit your existing events'
                },
                {
                    'title': 'View Payments',
                    'url': 'promoter:payment_list',
                    'icon': 'fas fa-credit-card',
                    'color': 'success',
                    'description': 'Check your payment history and balance'
                },
                {
                    'title': 'Promo Codes',
                    'url': 'promoter:promo_codes_list',
                    'icon': 'fas fa-tags',
                    'color': 'warning',
                    'description': 'Create and manage discount codes'
                },
                {
                    'title': 'Subscription',
                    'url': 'promoter:subscription_management',
                    'icon': 'fas fa-user-cog',
                    'color': 'secondary',
                    'description': 'Manage your subscription and billing'
                },
            ]
        }
        
        return render(request, 'promoter/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Unexpected error in promoter_dashboard: {e}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def subscription_management(request):
    """
    Subscription management page for promoters
    """
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        promoter = request.user.promoter
        
        # Get or create subscription
        subscription, created = Subscription.objects.get_or_create(
            promoter=promoter,
            defaults={
                'plan': 'pro',
                'status': 'active',
                'next_billing_date': timezone.now() + timedelta(days=30),
            }
        )
        
        context = {
            'promoter': promoter,
            'subscription': subscription,
        }
        
        return render(request, 'subscription/subscription_management.html', context)
        
    except Exception as e:
        logger.error(f"Unexpected error in subscription_management: {e}")
        messages.error(request, "An error occurred while loading subscription information.")
        return redirect('promoter:promoter_dashboard')


@login_required(login_url='/promoter/account/login/')
def cancel_subscription(request):
    """
    Cancel promoter subscription
    """
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        if request.method == 'POST':
            promoter = request.user.promoter
            
            try:
                subscription = Subscription.objects.get(promoter=promoter)
                
                # Get cancellation reason from form
                cancellation_reason = request.POST.get('cancellation_reason', '')
                
                # Cancel the subscription
                subscription.cancel(reason=cancellation_reason if cancellation_reason else None)
                
                # Send cancellation confirmation email
                try:
                    from django.core.mail import EmailMessage
                    from django.template.loader import render_to_string
                    
                    subject = "Subscription Cancelled - Eventlinez"
                    message = render_to_string('subscription/emails/cancellation_confirmation.html', {
                        'promoter': promoter,
                        'subscription': subscription,
                    })
                    
                    email = EmailMessage(
                        subject=subject,
                        body=message,
                        from_email="noreply@eventlinez.com",
                        to=[promoter.user.email],
                    )
                    email.content_subtype = "html"
                    email.send()
                    
                    logger.info(f"Cancellation confirmation email sent to {promoter.user.email}")
                except Exception as e:
                    logger.error(f"Failed to send cancellation email to {promoter.user.email}: {e}")
                
                # Log the cancellation
                logger.info(f"Subscription cancelled for promoter {promoter.user.email}. Reason: {cancellation_reason}")
                
                messages.success(
                    request, 
                    f'Your subscription has been cancelled successfully. '
                    f'You will continue to have access until {subscription.expires_date.strftime("%B %d, %Y")} '
                    f'and can reactivate anytime before then. A confirmation email has been sent to you.'
                )
                
                return redirect('promoter:subscription_management')
                
            except Subscription.DoesNotExist:
                messages.error(request, "No active subscription found.")
                return redirect('promoter:subscription_management')
        else:
            return redirect('promoter:subscription_management')
            
    except Exception as e:
        logger.error(f"Unexpected error in cancel_subscription: {e}")
        messages.error(request, "An error occurred while cancelling your subscription.")
        return redirect('promoter:subscription_management')


@login_required(login_url='/promoter/account/login/')
def reactivate_subscription(request):
    """
    Reactivate a cancelled subscription
    """
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            logger.error(f"User {request.user.username} does not have promoter profile")
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        if request.method == 'POST':
            promoter = request.user.promoter
            
            try:
                subscription = Subscription.objects.get(promoter=promoter)
                
                if subscription.reactivate():
                    logger.info(f"Subscription reactivated for promoter {promoter.user.email}")
                    messages.success(
                        request, 
                        'Your subscription has been reactivated successfully! '
                        f'Your next billing date is {subscription.next_billing_date.strftime("%B %d, %Y")}.'
                    )
                else:
                    messages.error(request, "Unable to reactivate subscription. Please contact support.")
                
                return redirect('promoter:subscription_management')
                
            except Subscription.DoesNotExist:
                messages.error(request, "No subscription found.")
                return redirect('promoter:subscription_management')
        else:
            return redirect('promoter:subscription_management')
            
    except Exception as e:
        logger.error(f"Unexpected error in reactivate_subscription: {e}")
        messages.error(request, "An error occurred while reactivating your subscription.")
        return redirect('promoter:subscription_management')
