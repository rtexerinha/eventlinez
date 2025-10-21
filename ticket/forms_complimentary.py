"""
Forms for Complimentary Ticket / Guest List Management
"""
from django import forms
from .models_complimentary import ComplimentaryTicket


class ComplimentaryTicketForm(forms.ModelForm):
    """
    Form for promoters to create complimentary tickets
    """
    
    class Meta:
        model = ComplimentaryTicket
        fields = ['guest_name', 'guest_email', 'guest_phone', 'ticket_type', 'notes']
        widgets = {
            'guest_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'John Doe',
                'required': True
            }),
            'guest_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'john@example.com',
                'required': True
            }),
            'guest_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+1 (555) 123-4567'
            }),
            'ticket_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes (not shown to guest)'
            }),
        }
        labels = {
            'guest_name': 'Guest Name',
            'guest_email': 'Guest Email',
            'guest_phone': 'Phone Number (Optional)',
            'ticket_type': 'Ticket Type',
            'notes': 'Internal Notes',
        }
        help_texts = {
            'guest_email': 'The complimentary ticket will be sent to this email address',
            'ticket_type': 'Select the type of complimentary ticket',
            'notes': 'These notes are only visible to you and your staff',
        }
    
    def clean_guest_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('guest_email')
        if email:
            email = email.lower().strip()
        return email
    
    def clean_guest_name(self):
        """Clean and validate guest name"""
        name = self.cleaned_data.get('guest_name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('Guest name must be at least 2 characters')
        return name


class BulkComplimentaryTicketForm(forms.Form):
    """
    Form for creating multiple complimentary tickets at once
    Useful for importing guest lists
    """
    
    guest_list = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 10,
            'placeholder': 'Enter one guest per line in format:\nName, Email, Phone\n\nExample:\nJohn Doe, john@example.com, +1-555-1234\nJane Smith, jane@example.com'
        }),
        label='Guest List',
        help_text='Enter one guest per line. Format: Name, Email, Phone (phone is optional)',
        required=True
    )
    
    ticket_type = forms.ChoiceField(
        choices=ComplimentaryTicket.TICKET_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Ticket Type for All Guests',
        initial='GUEST_LIST'
    )
    
    send_immediately = forms.BooleanField(
        required=False,
        initial=True,
        label='Send tickets immediately',
        help_text='If checked, tickets will be sent to guests via email right away'
    )
    
    def clean_guest_list(self):
        """Parse and validate the guest list"""
        guest_list_text = self.cleaned_data.get('guest_list')
        if not guest_list_text:
            raise forms.ValidationError('Guest list cannot be empty')
        
        guests = []
        errors = []
        
        for line_num, line in enumerate(guest_list_text.split('\n'), 1):
            line = line.strip()
            if not line:
                continue
            
            parts = [p.strip() for p in line.split(',')]
            
            if len(parts) < 2:
                errors.append(f'Line {line_num}: Invalid format. Need at least Name and Email')
                continue
            
            name = parts[0]
            email = parts[1]
            phone = parts[2] if len(parts) > 2 else ''
            
            # Validate email
            if '@' not in email or '.' not in email:
                errors.append(f'Line {line_num}: Invalid email format: {email}')
                continue
            
            # Validate name
            if len(name) < 2:
                errors.append(f'Line {line_num}: Name too short: {name}')
                continue
            
            guests.append({
                'name': name,
                'email': email.lower(),
                'phone': phone
            })
        
        if errors:
            raise forms.ValidationError('\n'.join(errors))
        
        if not guests:
            raise forms.ValidationError('No valid guests found in the list')
        
        return guests


class ComplimentaryTicketSearchForm(forms.Form):
    """
    Form for searching/filtering complimentary tickets
    """
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or email...'
        })
    )
    
    ticket_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(ComplimentaryTicket.TICKET_TYPE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + list(ComplimentaryTicket.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

