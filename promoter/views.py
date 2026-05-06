import logging
from django.contrib import messages
from os import path
from django.contrib.auth import update_session_auth_hash, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
import xlsxwriter
from django.http import StreamingHttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, Case, When, DecimalField
from datetime import datetime, timedelta
from decimal import Decimal

from customer.forms import SignUpFormPromoter, SignInPromoterForm
from event.forms import PromoterForm, ResetPasswordForm, VendorForm
from event.models import Promoter, Event
from promoter.forms import BankAccountForm, PromoCodeForm
from promoter.models import Payment, Vendor, SalesByVendor, BankAccount, get_balance, PromoCode
from ticket.models import Ticket

# Import the models that were causing issues when imported inside views
try:
    from ticket.models_complimentary import ComplimentaryTicket
except ImportError:
    ComplimentaryTicket = None

try:
    from order.models import OrderItem
except ImportError:
    OrderItem = None

try:
    from promoter.models import PromoCodeUsage
except ImportError:
    PromoCodeUsage = None

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
                    'title': 'Revenue Report',
                    'url': 'promoter:revenue_report',
                    'icon': 'fas fa-chart-line',
                    'color': 'warning',
                    'description': 'View detailed financial reports and sales analytics'
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
                    'title': 'Guest Lists',
                    'url': 'promoter:guest_lists_overview',
                    'icon': 'fas fa-list-ul',
                    'color': 'success',
                    'description': 'Manage complimentary tickets and VIP guest lists'
                },
            ]
        }
        
        return render(request, 'promoter/dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Unexpected error in promoter_dashboard: {e}")
        messages.error(request, "An error occurred while loading the dashboard.")
        return redirect('promoter:signup_promoter')


@login_required(login_url='/promoter/account/login/')
def revenue_report(request):
    """
    Revenue Report showing financial sales details by event
    """
    try:
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        promoter = request.user.promoter
        selected_event = None
        revenue_data = {}
        
        # Get all events for the dropdown
        events = Event.objects.filter(promoter=promoter).order_by('-created')
        
        # Handle both POST and GET requests for event selection
        event_id = request.POST.get('events_choice') or request.GET.get('event_id')
            
        if event_id:
            try:
                selected_event = Event.objects.get(pk=event_id, promoter=promoter)
                
                # Regular (non-Full Pass) tickets for this event + Full Pass tickets for this
                # specific day. Full Pass tickets are matched only via day_event so selecting
                # the Day-1 event never shows Day-2 or Day-3 tickets.
                from django.db.models import Q as _Q
                tickets_sold = Ticket.objects.filter(
                    _Q(event_ticket__event=selected_event, day_number__isnull=True) |
                    _Q(day_event=selected_event)
                ).select_related('order_item', 'event_ticket', 'customer', 'day_event').order_by('-created_at')

                # Calculate totals
                gross_revenue = Decimal('0.00')
                total_promo_discount = Decimal('0.00')

                # Build detailed ticket information
                ticket_details = []
                for ticket in tickets_sold:
                    # ticket.price is already the correct value: full price for regular tickets,
                    # or the per-day split amount for Full Pass tickets.
                    ticket_price = ticket.price or Decimal('0.00')
                    gross_revenue += ticket_price

                    # Get promo code and discount info
                    promo_code_used = ''
                    discount_amount = Decimal('0.00')

                    if hasattr(ticket, 'order_item') and ticket.order_item:
                        promo_code_used = ticket.order_item.promo_code or ''

                        # Discount only applies when a promo code was actually used and the
                        # unit_price (original face value) exceeds what the customer paid.
                        if promo_code_used and ticket.order_item.unit_price and ticket.order_item.unit_price > ticket_price:
                            discount_amount = ticket.order_item.unit_price - ticket_price
                            total_promo_discount += discount_amount
                    
                    # Get customer information
                    customer_name = 'Guest'
                    customer_email = ''
                    
                    if ticket.customer:
                        try:
                            if hasattr(ticket.customer, 'get_full_name'):
                                customer_name = ticket.customer.get_full_name()
                            elif hasattr(ticket.customer, 'first_name'):
                                customer_name = f"{getattr(ticket.customer, 'first_name', '')} {getattr(ticket.customer, 'last_name', '')}".strip()
                            
                            if not customer_name:
                                customer_name = str(ticket.customer)
                                
                            customer_email = getattr(ticket.customer, 'email', '')
                        except:
                            customer_name = 'Customer'
                    
                    # Use guest name if available
                    if not customer_name or customer_name.strip() in ['', 'Customer']:
                        customer_name = ticket.guest_name or 'Guest'
                    
                    original_price = ticket_price + discount_amount
                    
                    ticket_details.append({
                        'customer_name': customer_name,
                        'customer_email': customer_email,
                        'ticket_type': ticket.event_ticket.name,
                        'original_price': original_price,
                        'promo_code': promo_code_used,
                        'discount_amount': discount_amount,
                        'final_price': ticket_price,
                        'purchase_date': ticket.created_at
                    })
                
                # Calculate net revenue
                net_revenue = gross_revenue - total_promo_discount
                total_tickets_sold = len(ticket_details)
                
                revenue_data = {
                    'gross_revenue': gross_revenue,
                    'total_promo_discount': total_promo_discount,
                    'net_revenue': net_revenue,
                    'total_tickets_sold': total_tickets_sold,
                    'ticket_details': ticket_details
                }
                
            except Event.DoesNotExist:
                messages.error(request, "Event not found.")
            except Exception as e:
                logger.error(f"Error processing event data: {e}")
                messages.error(request, "Error loading event data.")
        
        context = {
            'events': events,
            'selected_event': selected_event,
            'revenue_data': revenue_data,
            'promoter': promoter,
            'today': timezone.now().date(),
        }

        return render(request, 'reports/revenue_report.html', context)
        
    except Exception as e:
        logger.error(f"Error in revenue_report: {e}")
        messages.error(request, "An error occurred while generating the revenue report.")
        return redirect('promoter:promoter_dashboard')


@login_required(login_url='/promoter/account/login/')
def revenue_report_export(request, event_id):
    """
    Export revenue report to Excel
    """
    try:
        # Check if user has promoter profile first
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        promoter = request.user.promoter
        selected_event = get_object_or_404(Event, pk=event_id, promoter=promoter)
        
        # Create response
        output = BytesIO()
        response = StreamingHttpResponse(
            output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=revenue_report_{selected_event.slug}_{timezone.now().strftime("%Y%m%d")}.xlsx'
        
        # Create workbook
        workbook = xlsxwriter.Workbook(output)
        
        # Styles
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'bg_color': '#d90075', 'font_color': 'white',
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        money_format = workbook.add_format({
            'num_format': '$#,##0.00', 'align': 'right', 'border': 1
        })
        number_format = workbook.add_format({
            'num_format': '#,##0', 'align': 'right', 'border': 1
        })
        text_format = workbook.add_format({
            'align': 'left', 'border': 1
        })
        
        # Summary Sheet
        summary_sheet = workbook.add_worksheet('Revenue Summary')
        summary_sheet.set_column('A:A', 25)
        summary_sheet.set_column('B:B', 15)
        
        # Same filter as the HTML report: regular tickets + Full Pass for this specific day only.
        from django.db.models import Q as _Q
        tickets_sold = Ticket.objects.filter(
            _Q(event_ticket__event=selected_event, day_number__isnull=True) |
            _Q(day_event=selected_event)
        ).select_related('order_item', 'customer', 'event_ticket')

        gross_revenue = tickets_sold.aggregate(total=Sum('price'))['total'] or Decimal('0.00')
        
        # Use conditional check for PromoCodeUsage
        if PromoCodeUsage:
            promo_usage = PromoCodeUsage.objects.filter(promo_code__event=selected_event)
            total_promo_discount = promo_usage.aggregate(total=Sum('discount_amount'))['total'] or Decimal('0.00')
        else:
            promo_usage = []
            total_promo_discount = Decimal('0.00')
            
        net_revenue = gross_revenue - total_promo_discount
        
        # Write summary
        row = 0
        summary_sheet.write(row, 0, f'Revenue Report - {selected_event.name}', title_format)
        row += 2
        
        summary_sheet.write(row, 0, 'Event Name:', header_format)
        summary_sheet.write(row, 1, selected_event.name, text_format)
        row += 1
        
        summary_sheet.write(row, 0, 'Event Date:', header_format)
        summary_sheet.write(row, 1, selected_event.event_date.strftime('%Y-%m-%d %H:%M'), text_format)
        row += 1
        
        summary_sheet.write(row, 0, 'Report Generated:', header_format)
        summary_sheet.write(row, 1, timezone.now().strftime('%Y-%m-%d %H:%M'), text_format)
        row += 2
        
        summary_sheet.write(row, 0, 'Gross Revenue:', header_format)
        summary_sheet.write(row, 1, float(gross_revenue), money_format)
        row += 1
        
        summary_sheet.write(row, 0, 'Total Promo Discounts:', header_format)
        summary_sheet.write(row, 1, float(total_promo_discount), money_format)
        row += 1
        
        summary_sheet.write(row, 0, 'Net Revenue:', header_format)
        summary_sheet.write(row, 1, float(net_revenue), money_format)
        row += 1
        
        summary_sheet.write(row, 0, 'Total Tickets Sold:', header_format)
        summary_sheet.write(row, 1, tickets_sold.count(), number_format)
        row += 1
        
        # Ticket Details Sheet
        details_sheet = workbook.add_worksheet('Ticket Details')
        details_sheet.set_column('A:A', 15)
        details_sheet.set_column('B:B', 30)
        details_sheet.set_column('C:C', 15)
        details_sheet.set_column('D:D', 15)
        details_sheet.set_column('E:E', 20)
        details_sheet.set_column('F:F', 15)
        
        # Headers
        headers = ['Ticket ID', 'Ticket Type', 'Price', 'Promo Code', 'Purchase Date', 'Customer']
        for col, header in enumerate(headers):
            details_sheet.write(0, col, header, header_format)
        
        # Data
        row = 1
        for ticket in tickets_sold:
            details_sheet.write(row, 0, ticket.id, number_format)
            details_sheet.write(row, 1, ticket.event_ticket.name, text_format)
            details_sheet.write(row, 2, float(ticket.price or Decimal('0.00')), money_format)
            
            # Safe access to order_item promo_code
            promo_code = ''
            if hasattr(ticket, 'order_item') and ticket.order_item and hasattr(ticket.order_item, 'promo_code'):
                promo_code = ticket.order_item.promo_code or ''
            
            details_sheet.write(row, 3, promo_code, text_format)
            details_sheet.write(row, 4, ticket.created_at.strftime('%Y-%m-%d %H:%M'), text_format)
            details_sheet.write(row, 5, str(ticket.customer), text_format)
            row += 1
        
        # Promo Codes Sheet - only if PromoCodeUsage is available
        if PromoCodeUsage and promo_usage:
            promo_sheet = workbook.add_worksheet('Promo Code Usage')
            promo_sheet.set_column('A:A', 15)
            promo_sheet.set_column('B:B', 20)
            promo_sheet.set_column('C:C', 15)
            promo_sheet.set_column('D:D', 20)
            
            # Headers
            promo_headers = ['Promo Code', 'Customer Email', 'Discount Amount', 'Used Date']
            for col, header in enumerate(promo_headers):
                promo_sheet.write(0, col, header, header_format)
            
            # Data
            row = 1
            for usage in promo_usage.order_by('-used_at'):
                promo_sheet.write(row, 0, usage.promo_code.code, text_format)
                promo_sheet.write(row, 1, usage.customer_email, text_format)
                promo_sheet.write(row, 2, float(usage.discount_amount), money_format)
                promo_sheet.write(row, 3, usage.used_at.strftime('%Y-%m-%d %H:%M'), text_format)
                row += 1
        
        workbook.close()
        output.seek(0)
        return response
        
    except Exception as e:
        logger.error(f"Error exporting revenue report: {e}")
        messages.error(request, "An error occurred while exporting the revenue report.")
        return redirect('promoter:revenue_report')


@login_required(login_url='/promoter/account/login/')
def guest_lists_overview(request):
    """
    Guest Lists Overview - Select an event to view its guest list
    """
    try:
        # Check authentication first
        if not request.user.is_authenticated:
            return redirect('promoter:signin_promoter')
            
        # Check if user has promoter profile
        try:
            promoter = request.user.promoter
            if not promoter:
                messages.error(request, "You need to have a promoter profile to access this page.")
                return redirect('promoter:signup_promoter')
        except AttributeError:
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
            
        selected_event = None
        guest_list_data = {}
        
        # Get all events for the dropdown
        events = Event.objects.filter(promoter=promoter).order_by('-created')
        
        # Handle event selection
        event_id = request.POST.get('events_choice') or request.GET.get('event_id')
        
        if event_id and ComplimentaryTicket:
            try:
                selected_event = Event.objects.get(pk=event_id, promoter=promoter)
                
                # Get all complimentary tickets for this event
                complimentary_tickets = ComplimentaryTicket.objects.filter(event=selected_event)
                
                # Calculate statistics
                total_guests = complimentary_tickets.count()
                pending_tickets = complimentary_tickets.filter(status='PENDING').count()
                sent_tickets = complimentary_tickets.filter(status='SENT').count()
                checked_in_tickets = complimentary_tickets.filter(status='CHECKED_IN').count()
                cancelled_tickets = complimentary_tickets.filter(status='CANCELLED').count()
                
                # Recent guests (last 10)
                recent_guests = complimentary_tickets.order_by('-created_at')[:10]
                
                # Guest statistics by ticket type
                ticket_types_stats = {}
                for ticket in complimentary_tickets:
                    try:
                        ticket_type = ticket.get_ticket_type_display()
                        if ticket_type not in ticket_types_stats:
                            ticket_types_stats[ticket_type] = {
                                'total': 0,
                                'checked_in': 0,
                                'pending': 0,
                                'sent': 0,
                                'cancelled': 0
                            }
                        ticket_types_stats[ticket_type]['total'] += 1
                        if hasattr(ticket, 'status'):
                            status_key = ticket.status.lower() if ticket.status else 'pending'
                            if status_key in ticket_types_stats[ticket_type]:
                                ticket_types_stats[ticket_type][status_key] += 1
                    except Exception as e:
                        logger.warning(f"Error processing ticket type stats: {e}")
                        continue
                
                guest_list_data = {
                    'total_guests': total_guests,
                    'pending_tickets': pending_tickets,
                    'sent_tickets': sent_tickets,
                    'checked_in_tickets': checked_in_tickets,
                    'cancelled_tickets': cancelled_tickets,
                    'recent_guests': recent_guests,
                    'ticket_types_stats': ticket_types_stats,
                    'complimentary_tickets': complimentary_tickets
                }
                
            except Event.DoesNotExist:
                messages.error(request, "Event not found.")
            except Exception as e:
                logger.error(f"Error loading guest list data: {e}")
                messages.error(request, "Error loading guest list data.")
        elif event_id and not ComplimentaryTicket:
            messages.warning(request, "Guest list functionality is not available - ComplimentaryTicket model not found.")
        
        context = {
            'events': events,
            'selected_event': selected_event,
            'guest_list_data': guest_list_data,
            'promoter': promoter,
            'complimentary_available': ComplimentaryTicket is not None,
            'today': timezone.now().date()
        }
        
        return render(request, 'guest_lists/guest_lists_overview.html', context)
        
    except Exception as e:
        logger.error(f"Error in guest_lists_overview: {e}")
        messages.error(request, "An error occurred while loading guest lists.")
        return redirect('promoter:promoter_dashboard')


# End of views.py

from promoter.models import Partner

@login_required(login_url='/promoter/account/login/')
def doorman_dashboard(request):
    """
    Doorman dashboard - shows assigned events for check-in
    No financial information displayed
    """
    user = request.user
    
    # Check if user is a doorman
    doorman_assignments = Partner.objects.filter(
        user=user,
        role='DOORMAN',
        disable=False
    ).select_related('event', 'event__city')
    
    if not doorman_assignments.exists() and not hasattr(user, 'promoter'):
        messages.error(request, "You don't have doorman access.")
        return redirect('shop:index')
    
    # Get events
    if hasattr(user, 'promoter'):
        # Promoter sees all their events
        events = Event.objects.filter(promoter=user.promoter)
        role = 'PROMOTER'
    else:
        # Doorman sees only assigned events
        event_ids = doorman_assignments.values_list('event_id', flat=True)
        events = Event.objects.filter(id__in=event_ids)
        role = 'DOORMAN'
    
    # Filter to current/upcoming events
    now = timezone.now()
    events = events.filter(event_date__gte=now - timedelta(hours=12)).order_by('event_date')
    
    # Add check-in stats to each event (no financial data)
    from ticket.models import Ticket
    try:
        from ticket.models_complimentary import ComplimentaryTicket
    except ImportError:
        ComplimentaryTicket = None
    
    events_data = []
    for event in events:
        # Paid tickets stats (no prices)
        paid_total = Ticket.objects.filter(event_ticket__event=event).count()
        paid_checked_in = Ticket.objects.filter(
            event_ticket__event=event,
            checkin_date__isnull=False
        ).count()
        
        # Guest list stats
        guest_total = 0
        guest_checked_in = 0
        if ComplimentaryTicket:
            guest_total = ComplimentaryTicket.objects.filter(
                event=event
            ).exclude(status='CANCELLED').count()
            guest_checked_in = ComplimentaryTicket.objects.filter(
                event=event,
                status='CHECKED_IN'
            ).count()
        
        total_expected = paid_total + guest_total
        total_checked_in = paid_checked_in + guest_checked_in
        percentage = round((total_checked_in / total_expected * 100) if total_expected > 0 else 0, 1)
        
        events_data.append({
            'event': event,
            'paid_total': paid_total,
            'paid_checked_in': paid_checked_in,
            'guest_total': guest_total,
            'guest_checked_in': guest_checked_in,
            'total_expected': total_expected,
            'total_checked_in': total_checked_in,
            'percentage': percentage,
        })
    
    context = {
        'events_data': events_data,
        'role': role,
        'user': user,
    }
    
    return render(request, 'doorman/doorman_dashboard.html', context)


@login_required(login_url='/promoter/account/login/')
def doorman_checkin_page(request, event_id):
    """
    Doorman check-in page for a specific event
    Shows ticket list with check-in functionality
    No financial information displayed
    """
    user = request.user
    
    # Verify access
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        messages.error(request, "Event not found.")
        return redirect('promoter:doorman_dashboard')
    
    # Check if user has access to this event
    has_access = False
    if hasattr(user, 'promoter') and event.promoter == user.promoter:
        has_access = True
    elif Partner.objects.filter(
        user=user,
        event=event,
        role='DOORMAN',
        disable=False
    ).exists():
        has_access = True
    
    if not has_access:
        messages.error(request, "You don't have access to this event.")
        return redirect('promoter:doorman_dashboard')
    
    # Get tickets
    from ticket.models import Ticket
    try:
        from ticket.models_complimentary import ComplimentaryTicket
    except ImportError:
        ComplimentaryTicket = None
    
    # Search functionality
    search_query = request.GET.get('q', '')
    
    # Regular tickets by their event; Full Pass tickets by day_event only
    paid_tickets = Ticket.objects.filter(
        Q(event_ticket__event=event, day_event__isnull=True) | Q(day_event=event)
    ).select_related('event_ticket', 'customer').order_by('-created_at')
    
    if search_query:
        paid_tickets = paid_tickets.filter(
            Q(guest_name__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(id__icontains=search_query)
        )
    
    # Guest list tickets
    guest_tickets = []
    if ComplimentaryTicket:
        guest_tickets = ComplimentaryTicket.objects.filter(
            event=event
        ).exclude(status='CANCELLED').order_by('-created_at')
        
        if search_query:
            guest_tickets = guest_tickets.filter(
                Q(guest_name__icontains=search_query) |
                Q(guest_email__icontains=search_query)
            )
    
    # Stats — same scoping rule: regular tickets by event, Full Pass by day_event
    _paid_qs = Ticket.objects.filter(
        Q(event_ticket__event=event, day_event__isnull=True) | Q(day_event=event)
    )
    paid_total = _paid_qs.count()
    paid_checked_in = _paid_qs.filter(checkin_date__isnull=False).count()
    
    guest_total = 0
    guest_checked_in = 0
    if ComplimentaryTicket:
        guest_total = ComplimentaryTicket.objects.filter(
            event=event
        ).exclude(status='CANCELLED').count()
        guest_checked_in = ComplimentaryTicket.objects.filter(
            event=event,
            status='CHECKED_IN'
        ).count()
    
    context = {
        'event': event,
        'paid_tickets': paid_tickets[:50],  # Limit to 50 for performance
        'guest_tickets': guest_tickets[:50],
        'search_query': search_query,
        'stats': {
            'paid_total': paid_total,
            'paid_checked_in': paid_checked_in,
            'guest_total': guest_total,
            'guest_checked_in': guest_checked_in,
            'total_expected': paid_total + guest_total,
            'total_checked_in': paid_checked_in + guest_checked_in,
        }
    }
    
    return render(request, 'doorman/doorman_checkin.html', context)


@login_required(login_url='/promoter/account/login/')
def partners_list(request):
    """
    List all partners (Business Partners and Doormen) for the promoter
    """
    try:
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
        
        promoter = request.user.promoter
        
        # Get all partners for events owned by this promoter
        partners = Partner.objects.filter(
            event__promoter=promoter
        ).select_related('user', 'event').order_by('-created_at')
        
        # Filter by role if specified
        role_filter = request.GET.get('role')
        if role_filter:
            partners = partners.filter(role=role_filter)
        
        # Filter by event if specified
        event_filter = request.GET.get('event')
        if event_filter:
            partners = partners.filter(event_id=event_filter)
        
        # Get events for filter dropdown
        events = Event.objects.filter(promoter=promoter).order_by('-event_date')
        
        context = {
            'partners': partners,
            'events': events,
            'role_filter': role_filter,
            'event_filter': event_filter,
            'promoter': promoter,
        }
        
        return render(request, 'partners/partners_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in partners_list: {e}")
        messages.error(request, "An error occurred while loading partners.")
        return redirect('promoter:promoter_dashboard')


@login_required(login_url='/promoter/account/login/')
def partner_create(request):
    """
    Create a new Business Partner - creates user account and assigns to event
    """
    try:
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
        
        promoter = request.user.promoter
        
        if request.method == 'POST':
            from promoter.forms import CreatePartnerWithUserForm
            form = CreatePartnerWithUserForm(request.POST, promoter=promoter)
            
            if form.is_valid():
                partner = form.save()
                
                role_name = partner.get_role_display()
                messages.success(
                    request, 
                    f'{role_name} "{partner.user.get_full_name()}" ({partner.email}) has been created and assigned to event "{partner.event.name}"'
                )
                return redirect('promoter:partners_list')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
        else:
            from promoter.forms import CreatePartnerWithUserForm
            form = CreatePartnerWithUserForm(promoter=promoter)
        
        return render(request, 'partners/partner_create.html', {
            'form': form,
            'promoter': promoter,
            'partner_type': 'Partner'
        })
        
    except Exception as e:
        logger.error(f"Error in partner_create: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('promoter:partners_list')


@login_required(login_url='/promoter/account/login/')
def doorman_create(request):
    """
    Create a new Doorman - creates user account and assigns to event with DOORMAN role
    """
    try:
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
        
        promoter = request.user.promoter
        
        if request.method == 'POST':
            from promoter.forms import CreatePartnerWithUserForm
            form = CreatePartnerWithUserForm(request.POST, promoter=promoter, role='DOORMAN')
            
            if form.is_valid():
                partner = form.save()
                
                messages.success(
                    request,
                    f'Doorman "{partner.user.get_full_name()}" ({partner.email}) has been created and assigned to event "{partner.event.name}"'
                )
                return redirect('promoter:partners_list')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{error}")
        else:
            from promoter.forms import CreatePartnerWithUserForm
            form = CreatePartnerWithUserForm(promoter=promoter, role='DOORMAN')
        
        return render(request, 'partners/partner_create.html', {
            'form': form,
            'promoter': promoter,
            'partner_type': 'Doorman'
        })
        
    except Exception as e:
        logger.error(f"Error in doorman_create: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('promoter:partners_list')


@login_required(login_url='/promoter/account/login/')
def partner_toggle_status(request, partner_id):
    """
    Enable or disable a partner
    """
    try:
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
        
        promoter = request.user.promoter
        partner = get_object_or_404(
            Partner,
            id=partner_id,
            event__promoter=promoter
        )
        
        partner.disable = not partner.disable
        partner.save()
        
        status = "disabled" if partner.disable else "enabled"
        messages.success(
            request,
            f'{partner.get_role_display()} "{partner.email}" has been {status}'
        )
        
        return redirect('promoter:partners_list')
        
    except Exception as e:
        logger.error(f"Error in partner_toggle_status: {e}")
        messages.error(request, "An error occurred while updating partner status.")
        return redirect('promoter:partners_list')


@login_required(login_url='/promoter/account/login/')
def partner_delete(request, partner_id):
    """
    Delete a partner assignment
    """
    try:
        if not hasattr(request.user, 'promoter') or not request.user.promoter:
            messages.error(request, "You need to have a promoter profile to access this page.")
            return redirect('promoter:signup_promoter')
        
        promoter = request.user.promoter
        partner = get_object_or_404(
            Partner,
            id=partner_id,
            event__promoter=promoter
        )
        
        partner_email = partner.email
        partner_role = partner.get_role_display()
        event_name = partner.event.name
        
        if request.method == 'POST':
            partner.delete()
            messages.success(
                request,
                f'{partner_role} "{partner_email}" has been removed from event "{event_name}"'
            )
            return redirect('promoter:partners_list')
        
        return render(request, 'partners/partner_delete.html', {
            'partner': partner,
            'promoter': promoter
        })
        
    except Exception as e:
        logger.error(f"Error in partner_delete: {e}")
        messages.error(request, "An error occurred while deleting the partner.")
        return redirect('promoter:partners_list')

