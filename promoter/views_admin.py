"""
Admin-only views for the Payout Report.
Access is restricted to Django staff users (is_staff=True).
"""
import logging
from decimal import Decimal
from io import BytesIO

import xlsxwriter
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import EmailMessage
from django.db.models import Sum, Count
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib import messages

from event.models import Promoter, Event
from ticket.models import Ticket

try:
    from promoter.models import PromoCode, PromoCodeUsage, Payment, BankAccount
except ImportError:
    PromoCode = PromoCodeUsage = Payment = BankAccount = None

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_report_data(event):
    """
    Aggregate all report data for a given Event.
    Returns a dict consumed by both the HTML view and the Excel export.
    """
    fee_rate = Decimal(str(getattr(settings, 'EVENTLINEZ_FEE', 0.12)))

    # ── Tickets by type ──────────────────────────────────────────────────────
    from django.db.models import Q as _Q
    tickets_qs = Ticket.objects.filter(
        event_ticket__event=event
    ).select_related('event_ticket', 'order_item', 'customer')

    from event.models import Ticket as TicketType
    ticket_types = TicketType.objects.filter(event=event).order_by('name')

    ticket_breakdown = []
    gross_revenue = Decimal('0.00')

    for tt in ticket_types:
        days = getattr(tt, 'days', 1) or 1
        # Multi-day (Full Pass) tickets create one Ticket row per day per purchase.
        # Filter to day_number=1 (or NULL for regular tickets) so we count passes sold,
        # not individual day-slots.
        sold = tickets_qs.filter(event_ticket=tt).filter(
            _Q(day_number__isnull=True) | _Q(day_number=1)
        )
        qty = sold.count()
        if days > 1:
            # ticket.price holds the per-day split; order_item.unit_price is the full pass price
            subtotal = sold.aggregate(total=Sum('order_item__unit_price'))['total'] or Decimal('0.00')
        else:
            subtotal = sold.aggregate(total=Sum('price'))['total'] or Decimal('0.00')
        gross_revenue += subtotal
        if qty > 0:
            ticket_breakdown.append({
                'name': tt.name,
                'qty': qty,
                'unit_price': tt.price,
                'subtotal': subtotal,
            })

    # ── Promo code usage ─────────────────────────────────────────────────────
    promo_breakdown = []
    total_promo_discount = Decimal('0.00')

    if PromoCodeUsage and PromoCode:
        usages = (
            PromoCodeUsage.objects
            .filter(promo_code__event=event)
            .values(
                'promo_code__code',
                'promo_code__discount_type',
                'promo_code__discount_value',
            )
            .annotate(uses=Count('id'), total_discount=Sum('discount_amount'))
            .order_by('promo_code__code')
        )
        for u in usages:
            discount = u['total_discount'] or Decimal('0.00')
            total_promo_discount += discount
            promo_breakdown.append({
                'code': u['promo_code__code'],
                'discount_type': u['promo_code__discount_type'],
                'discount_value': u['promo_code__discount_value'],
                'uses': u['uses'],
                'total_discount': discount,
            })

    # ── Summary ──────────────────────────────────────────────────────────────
    net_revenue = gross_revenue - total_promo_discount
    platform_fee = (net_revenue * fee_rate).quantize(Decimal('0.01'))
    payout_amount = (net_revenue - platform_fee).quantize(Decimal('0.01'))

    # Payments already made to this promoter for this event (if tracked)
    payments_made = Decimal('0.00')
    if Payment:
        # Payments are per-promoter, not per-event; show total owed vs paid
        payments_made = (
            Payment.objects
            .filter(promoter=event.promoter)
            .aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        )

    # Bank account info
    bank = None
    if BankAccount:
        bank = BankAccount.objects.filter(promoter=event.promoter).first()

    return {
        'event': event,
        'promoter': event.promoter,
        'ticket_breakdown': ticket_breakdown,
        'promo_breakdown': promo_breakdown,
        'gross_revenue': gross_revenue,
        'total_promo_discount': total_promo_discount,
        'net_revenue': net_revenue,
        'fee_rate': fee_rate,
        'fee_rate_pct': (fee_rate * 100).quantize(Decimal('0.01')),
        'platform_fee': platform_fee,
        'payout_amount': payout_amount,
        'payments_made': payments_made,
        'bank': bank,
        'generated_at': timezone.now(),
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@staff_member_required
def payout_report(request):
    """
    Main payout report page.
    - Step 1: admin picks a promoter
    - Step 2: admin picks an event → full report rendered
    """
    promoters = Promoter.objects.order_by('name')
    events = []
    report_data = None
    selected_promoter = None
    selected_event = None

    promoter_id = request.GET.get('promoter_id') or request.POST.get('promoter_id')
    event_id = request.GET.get('event_id') or request.POST.get('event_id')

    if promoter_id:
        try:
            selected_promoter = Promoter.objects.get(pk=promoter_id)
            events = Event.objects.filter(promoter=selected_promoter).order_by('-event_date')
        except Promoter.DoesNotExist:
            pass

    if event_id and selected_promoter:
        try:
            selected_event = Event.objects.get(pk=event_id, promoter=selected_promoter)
            report_data = _build_report_data(selected_event)
        except Event.DoesNotExist:
            messages.error(request, "Event not found for this promoter.")

    context = {
        'title': 'Payout Report',
        'promoters': promoters,
        'events': events,
        'selected_promoter': selected_promoter,
        'selected_event': selected_event,
        'report_data': report_data,
        # Django admin sidebar needs these
        'has_permission': True,
    }
    return render(request, 'admin/payout_report.html', context)


@staff_member_required
def payout_report_events_ajax(request):
    """
    AJAX endpoint: return events for a given promoter as JSON.
    Used by the promoter dropdown's onchange handler.
    """
    promoter_id = request.GET.get('promoter_id')
    if not promoter_id:
        return JsonResponse({'events': []})
    try:
        promoter = Promoter.objects.get(pk=promoter_id)
    except Promoter.DoesNotExist:
        return JsonResponse({'events': []})

    events = (
        Event.objects
        .filter(promoter=promoter)
        .order_by('-event_date')
        .values('id', 'name', 'event_date', 'available')
    )
    data = [
        {
            'id': e['id'],
            'name': e['name'],
            'event_date': e['event_date'].strftime('%Y-%m-%d') if e['event_date'] else '',
            'available': e['available'],
        }
        for e in events
    ]
    return JsonResponse({'events': data})


@staff_member_required
def payout_report_export(request, event_id):
    """
    Export the payout report to Excel (.xlsx).
    """
    event = get_object_or_404(Event, pk=event_id)
    data = _build_report_data(event)

    output = BytesIO()
    wb = xlsxwriter.Workbook(output)

    # ── Formats ──────────────────────────────────────────────────────────────
    title_fmt = wb.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
    section_fmt = wb.add_format({'bold': True, 'font_size': 12, 'bg_color': '#d90075',
                                 'font_color': 'white', 'border': 1})
    header_fmt = wb.add_format({'bold': True, 'bg_color': '#444444',
                                'font_color': 'white', 'border': 1})
    money_fmt = wb.add_format({'num_format': '$#,##0.00', 'border': 1})
    number_fmt = wb.add_format({'num_format': '#,##0', 'border': 1})
    text_fmt = wb.add_format({'border': 1})
    pct_fmt = wb.add_format({'num_format': '0.00%', 'border': 1})
    bold_money_fmt = wb.add_format({'bold': True, 'num_format': '$#,##0.00', 'border': 1})

    # ── Summary Sheet ────────────────────────────────────────────────────────
    ws = wb.add_worksheet('Payout Summary')
    ws.set_column('A:A', 30)
    ws.set_column('B:B', 20)

    ws.merge_range('A1:B1', f'Payout Report — {event.name}', title_fmt)

    row = 2
    info = [
        ('Promoter', data['promoter'].name),
        ('Promoter Email', data['promoter'].email),
        ('Event', event.name),
        ('Event Date', event.event_date.strftime('%Y-%m-%d %H:%M')),
        ('Report Generated', data['generated_at'].strftime('%Y-%m-%d %H:%M')),
    ]
    for label, value in info:
        ws.write(row, 0, label, header_fmt)
        ws.write(row, 1, value, text_fmt)
        row += 1

    row += 1
    ws.write(row, 0, 'Gross Revenue', section_fmt)
    ws.write(row, 1, float(data['gross_revenue']), money_fmt)
    row += 1
    ws.write(row, 0, 'Total Promo Discounts', section_fmt)
    ws.write(row, 1, float(data['total_promo_discount']), money_fmt)
    row += 1
    ws.write(row, 0, 'Net Revenue', section_fmt)
    ws.write(row, 1, float(data['net_revenue']), money_fmt)
    row += 1
    ws.write(row, 0, f'Platform Fee ({data["fee_rate_pct"]}%)', section_fmt)
    ws.write(row, 1, float(data['platform_fee']), money_fmt)
    row += 1
    ws.write(row, 0, 'PAYOUT TO PROMOTER', wb.add_format({
        'bold': True, 'font_size': 13, 'bg_color': '#007AFF',
        'font_color': 'white', 'border': 2
    }))
    ws.write(row, 1, float(data['payout_amount']), wb.add_format({
        'bold': True, 'num_format': '$#,##0.00', 'border': 2, 'font_size': 13
    }))

    if data['bank']:
        row += 2
        ws.write(row, 0, 'Bank Name', header_fmt)
        ws.write(row, 1, data['bank'].bank_name, text_fmt)
        row += 1
        ws.write(row, 0, 'Routing Number', header_fmt)
        ws.write(row, 1, data['bank'].routing_number, text_fmt)
        row += 1
        ws.write(row, 0, 'Account Number', header_fmt)
        ws.write(row, 1, data['bank'].account_number, text_fmt)

    # ── Ticket Breakdown Sheet ───────────────────────────────────────────────
    ws2 = wb.add_worksheet('Ticket Breakdown')
    ws2.set_column('A:A', 30)
    ws2.set_column('B:B', 12)
    ws2.set_column('C:C', 15)
    ws2.set_column('D:D', 15)

    for col, h in enumerate(['Ticket Type', 'Qty Sold', 'Unit Price', 'Subtotal']):
        ws2.write(0, col, h, header_fmt)

    for i, tb in enumerate(data['ticket_breakdown'], 1):
        ws2.write(i, 0, tb['name'], text_fmt)
        ws2.write(i, 1, tb['qty'], number_fmt)
        ws2.write(i, 2, float(tb['unit_price']), money_fmt)
        ws2.write(i, 3, float(tb['subtotal']), money_fmt)

    # ── Promo Code Sheet ─────────────────────────────────────────────────────
    if data['promo_breakdown']:
        ws3 = wb.add_worksheet('Promo Codes Used')
        ws3.set_column('A:A', 20)
        ws3.set_column('B:B', 18)
        ws3.set_column('C:C', 15)
        ws3.set_column('D:D', 10)
        ws3.set_column('E:E', 18)

        for col, h in enumerate(['Code', 'Discount Type', 'Discount Value', 'Uses', 'Total Discount']):
            ws3.write(0, col, h, header_fmt)

        for i, pb in enumerate(data['promo_breakdown'], 1):
            ws3.write(i, 0, pb['code'], text_fmt)
            ws3.write(i, 1, pb['discount_type'].title(), text_fmt)
            ws3.write(i, 2, float(pb['discount_value']), money_fmt)
            ws3.write(i, 3, pb['uses'], number_fmt)
            ws3.write(i, 4, float(pb['total_discount']), money_fmt)

    wb.close()
    output.seek(0)

    filename = f'payout_{event.slug}_{timezone.now().strftime("%Y%m%d")}.xlsx'
    response = StreamingHttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@staff_member_required
def payout_report_send_email(request, event_id):
    """
    POST: email the payout report summary to the promoter.
    """
    if request.method != 'POST':
        return redirect('admin_payout_report')

    event = get_object_or_404(Event, pk=event_id)
    data = _build_report_data(event)
    promoter = data['promoter']

    try:
        subject = f'Eventlinez – Payout Report: {event.name}'
        body = render_to_string('admin/payout_report_email.html', data)

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[promoter.email],
        )
        email.content_subtype = 'html'
        email.send()

        messages.success(
            request,
            f'Payout report sent to {promoter.email} successfully.'
        )
    except Exception as e:
        logger.error(f'Error sending payout report email: {e}')
        messages.error(request, 'Failed to send email. Please try again.')

    return redirect(
        f'/admin/payout-report/?promoter_id={promoter.id}&event_id={event.id}'
    )
