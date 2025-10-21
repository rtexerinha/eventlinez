"""
Complimentary Ticket Model for Guest List / VIP / Free Tickets
These tickets bypass payment and are issued directly by promoters
"""
import uuid
from io import BytesIO

import qrcode
import qrcode.image.svg
from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

from event.models import Event
from eventlinez import settings


class ComplimentaryTicket(models.Model):
    """
    Complimentary/Free tickets for guest list, VIPs, press, etc.
    No payment required - issued directly by promoter
    """
    
    TICKET_TYPE_CHOICES = [
        ('GUEST_LIST', 'Guest List'),
        ('VIP', 'VIP'),
        ('PRESS', 'Press'),
        ('COMP', 'Complimentary'),
        ('STAFF', 'Staff'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('CHECKED_IN', 'Checked In'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Event relationship
    event = models.ForeignKey(
        Event, 
        on_delete=models.CASCADE,
        related_name='complimentary_tickets'
    )
    
    # Guest information
    guest_name = models.CharField(max_length=200)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20, blank=True)
    
    # Ticket details
    ticket_type = models.CharField(
        max_length=20,
        choices=TICKET_TYPE_CHOICES,
        default='GUEST_LIST'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    
    # Unique identifier for QR code
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    checkin_date = models.DateTimeField(null=True, blank=True)
    
    # Optional notes from promoter
    notes = models.TextField(blank=True, help_text='Internal notes about this guest')
    
    # Who issued this ticket
    issued_by = models.ForeignKey(
        'event.Promoter',
        on_delete=models.PROTECT,
        related_name='issued_complimentary_tickets'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Complimentary Ticket'
        verbose_name_plural = 'Complimentary Tickets'
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['uuid']),
            models.Index(fields=['guest_email']),
        ]
    
    def __str__(self):
        return f"{self.guest_name} - {self.event.name} ({self.get_ticket_type_display()})"
    
    def as_qrcode(self):
        """Generate QR code as SVG for display"""
        host = settings.APP_HOST
        content = f"{host}/promoter/ticket/complimentary/checkin/{self.uuid}"
        img = qrcode.make(content, image_factory=qrcode.image.svg.SvgImage, box_size=20)
        stream = BytesIO()
        img.save(stream)
        svg = mark_safe(stream.getvalue().decode())
        return svg
    
    def _qrcode_reportlab(self):
        """Generate QR code for PDF"""
        content = f"{settings.APP_HOST}/promoter/ticket/complimentary/checkin/{self.uuid}"
        qr_code = qr.QrCodeWidget(content)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        c = Drawing(45, 45, transform=[200. / width, 0, 0, 200. / height, 0, 0])
        c.add(qr_code)
        return c
    
    def as_pdf(self):
        """Generate complimentary ticket as PDF"""
        qrcodec = self._qrcode_reportlab()
        out = BytesIO()
        
        font_name = 'Helvetica'
        font_size = 10
        
        p = canvas.Canvas(out)
        p.setFont(font_name, font_size)
        p.setFillColor(HexColor('#565454'))
        
        p.setStrokeGray(0.8)
        p.rect(130, 780, 0, 0, fill=1)
        p.roundRect(130, 390, 300, 430, 10, stroke=1, fill=0)
        
        # Logo
        img_file = 'static/img/Eventlinez.png'
        try:
            p.drawImage(img_file, 230, 785, width=100, preserveAspectRatio=True, mask='auto')
        except:
            pass
        
        p.setStrokeGray(0.8)
        p.line(130, 780, 430, 780)
        p.setStrokeGray(0.6)
        
        # Guest Name
        p.setFont("Helvetica-Bold", 12)
        p.drawString(150, 755, self.guest_name)
        
        # Event Details
        p.setFont("Helvetica", 11)
        p.drawString(150, 730, 'Event:')
        p.setFont("Helvetica-Bold", 11)
        p.drawString(150, 715, str(self.event.name))
        
        # Ticket Type - Prominent "FREE TICKET" or ticket type
        p.setFont("Helvetica-Bold", 14)
        p.setFillColor(HexColor('#d90075'))
        if self.ticket_type == 'VIP':
            p.drawString(150, 685, 'VIP TICKET')
        elif self.ticket_type == 'PRESS':
            p.drawString(150, 685, 'PRESS TICKET')
        elif self.ticket_type == 'STAFF':
            p.drawString(150, 685, 'STAFF TICKET')
        else:
            p.drawString(150, 685, 'FREE TICKET')
        
        p.setFillColor(HexColor('#565454'))
        p.setFont("Helvetica", 10)
        
        # Date
        p.drawString(150, 655, 'Date:')
        p.setFont("Helvetica-Bold", 10)
        p.drawString(150, 640, self.event.event_date.strftime('%b %d, %Y at %I:%M %p'))
        
        # Address
        p.setFont("Helvetica", 10)
        p.drawString(150, 615, 'Address:')
        p.setFont("Helvetica-Bold", 10)
        p.drawString(150, 600, str(self.event.address))
        p.drawString(150, 585, f"{self.event.city.name}")
        
        # QR Code
        renderPDF.draw(qrcodec, p, 230, 450)
        
        # QR Code Label
        p.setFont("Helvetica", 9)
        p.drawCentredString(275, 435, 'Scan QR Code at Entry')
        
        # Ticket Info
        p.setFont("Helvetica", 8)
        p.drawString(150, 410, f'Ticket ID: {str(self.uuid)[:8]}...')
        
        # Footer
        p.setFont("Helvetica", 7)
        p.setFillColor(HexColor('#999999'))
        p.drawCentredString(280, 395, 'This ticket is non-transferable')
        
        p.showPage()
        p.save()
        
        pdf = out.getvalue()
        out.close()
        return pdf
    
    def check_in(self):
        """Mark ticket as checked in"""
        if self.checkin_date:
            return False, "Ticket already checked in"
        
        self.checkin_date = timezone.now()
        self.status = 'CHECKED_IN'
        self.save()
        return True, "Check-in successful"
    
    def mark_as_sent(self):
        """Mark ticket as sent to guest"""
        self.sent_at = timezone.now()
        self.status = 'SENT'
        self.save()
    
    def cancel(self):
        """Cancel this complimentary ticket"""
        self.status = 'CANCELLED'
        self.save()
    
    @property
    def is_valid(self):
        """Check if ticket is valid for check-in"""
        return self.status in ['PENDING', 'SENT'] and not self.checkin_date
    
    @property
    def qr_code_url(self):
        """Get the check-in URL for this ticket"""
        host = settings.APP_HOST
        return f"{host}/promoter/ticket/complimentary/checkin/{self.uuid}"

