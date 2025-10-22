"""
Views for Complimentary Ticket / Guest List Management
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db.models import Q
from django.conf import settings
from io import BytesIO
import urllib.parse

from event.models import Event
from .models_complimentary import ComplimentaryTicket
from .forms_complimentary import (
    ComplimentaryTicketForm,
    BulkComplimentaryTicketForm,
    ComplimentaryTicketSearchForm
)


@login_required(login_url='/promoter/account/login/')
def guest_list(request, event_id):
    """
    View and manage guest list for an event
    """
    # Get event and verify ownership
    event = get_object_or_404(Event, id=event_id, promoter=request.user.promoter)
    
    # Get all complimentary tickets for this event
    tickets = ComplimentaryTicket.objects.filter(event=event)
    
    # Apply search/filters
    search_form = ComplimentaryTicketSearchForm(request.GET)
    if search_form.is_valid():
        search = search_form.cleaned_data.get('search')
        ticket_type = search_form.cleaned_data.get('ticket_type')
        status = search_form.cleaned_data.get('status')
        
        if search:
            tickets = tickets.filter(
                Q(guest_name__icontains=search) | 
                Q(guest_email__icontains=search)
            )
        if ticket_type:
            tickets = tickets.filter(ticket_type=ticket_type)
        if status:
            tickets = tickets.filter(status=status)
    
    # Get statistics
    stats = {
        'total': tickets.count(),
        'pending': tickets.filter(status='PENDING').count(),
        'sent': tickets.filter(status='SENT').count(),
        'checked_in': tickets.filter(status='CHECKED_IN').count(),
        'cancelled': tickets.filter(status='CANCELLED').count(),
    }
    
    context = {
        'event': event,
        'tickets': tickets,
        'search_form': search_form,
        'stats': stats,
    }
    
    return render(request, 'ticket/guest_list.html', context)


@login_required(login_url='/promoter/account/login/')
def create_complimentary_ticket(request, event_id):
    """
    Create a single complimentary ticket
    """
    event = get_object_or_404(Event, id=event_id, promoter=request.user.promoter)
    
    if request.method == 'POST':
        form = ComplimentaryTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.event = event
            ticket.issued_by = request.user.promoter
            ticket.save()
            
            # Send email if requested
            send_email = request.POST.get('send_email') == 'on'
            if send_email:
                success = send_complimentary_ticket_email(ticket)
                if success:
                    ticket.mark_as_sent()
                    messages.success(request, f'Complimentary ticket created and sent to {ticket.guest_email}')
                else:
                    messages.warning(request, f'Ticket created but email failed to send to {ticket.guest_email}')
            else:
                messages.success(request, f'Complimentary ticket created for {ticket.guest_name}')
            
            return redirect('promoter:guest_list', event_id=event.id)
    else:
        form = ComplimentaryTicketForm()
    
    context = {
        'event': event,
        'form': form,
    }
    
    return render(request, 'ticket/create_complimentary_ticket.html', context)


@login_required(login_url='/promoter/account/login/')
def bulk_create_complimentary_tickets(request, event_id):
    """
    Create multiple complimentary tickets from a list
    """
    event = get_object_or_404(Event, id=event_id, promoter=request.user.promoter)
    
    if request.method == 'POST':
        form = BulkComplimentaryTicketForm(request.POST)
        if form.is_valid():
            guests = form.cleaned_data['guest_list']
            ticket_type = form.cleaned_data['ticket_type']
            send_immediately = form.cleaned_data['send_immediately']
            
            created_count = 0
            sent_count = 0
            
            for guest in guests:
                ticket = ComplimentaryTicket.objects.create(
                    event=event,
                    guest_name=guest['name'],
                    guest_email=guest['email'],
                    guest_phone=guest['phone'],
                    ticket_type=ticket_type,
                    issued_by=request.user.promoter
                )
                created_count += 1
                
                if send_immediately:
                    if send_complimentary_ticket_email(ticket):
                        ticket.mark_as_sent()
                        sent_count += 1
            
            if send_immediately:
                messages.success(request, f'Created {created_count} tickets and sent {sent_count} emails')
            else:
                messages.success(request, f'Created {created_count} complimentary tickets')
            
            return redirect('promoter:guest_list', event_id=event.id)
    else:
        form = BulkComplimentaryTicketForm()
    
    context = {
        'event': event,
        'form': form,
    }
    
    return render(request, 'ticket/bulk_create_complimentary_tickets.html', context)


@login_required(login_url='/promoter/account/login/')
def view_complimentary_ticket(request, ticket_id):
    """
    View a single complimentary ticket
    """
    ticket = get_object_or_404(
        ComplimentaryTicket, 
        id=ticket_id,
        event__promoter=request.user.promoter
    )
    
    context = {
        'ticket': ticket,
    }
    
    return render(request, 'ticket/view_complimentary_ticket.html', context)


@login_required(login_url='/promoter/account/login/')
def download_complimentary_ticket_pdf(request, ticket_id):
    """
    Download complimentary ticket as PDF
    """
    ticket = get_object_or_404(
        ComplimentaryTicket,
        id=ticket_id,
        event__promoter=request.user.promoter
    )
    
    pdf = ticket.as_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{ticket.uuid}.pdf"'
    
    return response


@login_required(login_url='/promoter/account/login/')
def send_complimentary_ticket_email_view(request, ticket_id):
    """
    Resend complimentary ticket email
    """
    ticket = get_object_or_404(
        ComplimentaryTicket,
        id=ticket_id,
        event__promoter=request.user.promoter
    )
    
    if send_complimentary_ticket_email(ticket):
        ticket.mark_as_sent()
        messages.success(request, f'Ticket sent to {ticket.guest_email}')
    else:
        messages.error(request, 'Failed to send email')
    
    return redirect('promoter:guest_list', event_id=ticket.event.id)


@login_required(login_url='/promoter/account/login/')
def cancel_complimentary_ticket(request, ticket_id):
    """
    Cancel a complimentary ticket
    """
    ticket = get_object_or_404(
        ComplimentaryTicket,
        id=ticket_id,
        event__promoter=request.user.promoter
    )
    
    if ticket.checkin_date:
        messages.error(request, 'Cannot cancel a ticket that has already been checked in')
    else:
        ticket.cancel()
        messages.success(request, f'Ticket for {ticket.guest_name} has been cancelled')
    
    return redirect('promoter:guest_list', event_id=ticket.event.id)


def complimentary_ticket_checkin(request, uuid):
    """
    Check-in a complimentary ticket (can be accessed without login for QR scanning)
    """
    ticket = get_object_or_404(ComplimentaryTicket, uuid=uuid)
    
    if request.method == 'POST':
        if ticket.checkin_date:
            return JsonResponse({
                'success': False,
                'message': 'Ticket already checked in',
                'checked_in_at': ticket.checkin_date.isoformat()
            })
        
        success, message = ticket.check_in()
        
        return JsonResponse({
            'success': success,
            'message': message,
            'guest_name': ticket.guest_name,
            'ticket_type': ticket.get_ticket_type_display(),
            'event_name': ticket.event.name,
        })
    
    # GET request - show check-in page
    context = {
        'ticket': ticket,
    }
    return render(request, 'ticket/complimentary_checkin.html', context)


@login_required(login_url='/promoter/account/login/')
def download_complimentary_ticket_qr(request, ticket_id):
    """
    Download QR code as PNG image
    """
    ticket = get_object_or_404(
        ComplimentaryTicket,
        id=ticket_id,
        event__promoter=request.user.promoter
    )
    
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(ticket.qr_code_url)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Create a larger image with text
    img_width = 400
    img_height = 500
    img = Image.new('RGB', (img_width, img_height), 'white')
    
    # Paste QR code
    qr_img = qr_img.resize((300, 300))
    img.paste(qr_img, (50, 50))
    
    # Add text
    draw = ImageDraw.Draw(img)
    
    # Try to use a font, fallback to default
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Add guest name
    text = ticket.guest_name
    bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = bbox[2] - bbox[0]
    draw.text(((img_width - text_width) // 2, 370), text, fill='black', font=font_large)
    
    # Add event name
    text = ticket.event.name[:30]
    bbox = draw.textbbox((0, 0), text, font=font_medium)
    text_width = bbox[2] - bbox[0]
    draw.text(((img_width - text_width) // 2, 400), text, fill='black', font=font_medium)
    
    # Add ticket type
    text = ticket.get_ticket_type_display()
    bbox = draw.textbbox((0, 0), text, font=font_small)
    text_width = bbox[2] - bbox[0]
    draw.text(((img_width - text_width) // 2, 430), text, fill='gray', font=font_small)
    
    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="ticket_qr_{ticket.uuid}.png"'
    
    return response


@login_required(login_url='/promoter/account/login/')
def get_whatsapp_share_link(request, ticket_id):
    """
    Get WhatsApp share link for ticket
    """
    ticket = get_object_or_404(
        ComplimentaryTicket,
        id=ticket_id,
        event__promoter=request.user.promoter
    )
    
    # Create message
    message = f"""🎉 Your FREE Ticket for {ticket.event.name}

👤 Guest: {ticket.guest_name}
🎫 Type: {ticket.get_ticket_type_display()}
📅 Date: {ticket.event.event_date.strftime('%B %d, %Y at %I:%M %p')}
📍 Location: {ticket.event.address}, {ticket.event.city.name}

🔗 Your ticket: {ticket.qr_code_url}

Show this QR code at the entrance!"""
    
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # WhatsApp link
    if ticket.guest_phone:
        # Remove any non-digit characters from phone
        phone = ''.join(filter(str.isdigit, ticket.guest_phone))
        whatsapp_url = f"https://wa.me/{phone}?text={encoded_message}"
    else:
        # General WhatsApp share
        whatsapp_url = f"https://wa.me/?text={encoded_message}"
    
    return JsonResponse({
        'success': True,
        'whatsapp_url': whatsapp_url,
        'message': message
    })


@login_required(login_url='/promoter/account/login/')
def get_sms_link(request, ticket_id):
    """
    Get SMS link for ticket
    """
    ticket = get_object_or_404(
        ComplimentaryTicket,
        id=ticket_id,
        event__promoter=request.user.promoter
    )
    
    # Create SMS message
    message = f"Your FREE ticket for {ticket.event.name}. Show this at entrance: {ticket.qr_code_url}"
    
    # URL encode
    encoded_message = urllib.parse.quote(message)
    
    # SMS link (works on most mobile devices)
    if ticket.guest_phone:
        phone = ''.join(filter(str.isdigit, ticket.guest_phone))
        sms_url = f"sms:{phone}?body={encoded_message}"
    else:
        sms_url = f"sms:?body={encoded_message}"
    
    return JsonResponse({
        'success': True,
        'sms_url': sms_url,
        'message': message,
        'phone': ticket.guest_phone
    })


@login_required(login_url='/promoter/account/login/')
def share_ticket_options(request, ticket_id):
    """
    Show all share options for a ticket
    """
    ticket = get_object_or_404(
        ComplimentaryTicket,
        id=ticket_id,
        event__promoter=request.user.promoter
    )
    
    context = {
        'ticket': ticket,
    }
    
    return render(request, 'ticket/share_complimentary_ticket.html', context)


def send_complimentary_ticket_email(ticket):
    """
    Send complimentary ticket via email
    Returns True if successful, False otherwise
    """
    try:
        # Generate PDF
        pdf = ticket.as_pdf()
        
        # Prepare email context
        context = {
            'ticket': ticket,
            'event': ticket.event,
            'guest_name': ticket.guest_name,
            'ticket_type_display': ticket.get_ticket_type_display(),
        }
        
        # Render email templates
        subject = f'Your Free Ticket for {ticket.event.name}'
        html_message = render_to_string('ticket/emails/complimentary_ticket_email.html', context)
        text_message = render_to_string('ticket/emails/complimentary_ticket_email.txt', context)
        
        # Create email
        email = EmailMessage(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[ticket.guest_email],
        )
        
        # Attach HTML version
        email.content_subtype = 'html'
        email.body = html_message
        
        # Attach PDF ticket
        email.attach(
            f'ticket_{ticket.uuid}.pdf',
            pdf,
            'application/pdf'
        )
        
        # Send email
        email.send()
        
        return True
        
    except Exception as e:
        print(f"Error sending complimentary ticket email: {e}")
        return False

