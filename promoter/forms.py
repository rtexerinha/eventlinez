from django.forms import ModelForm
from promoter.models import BankAccount, Payment, get_balance, PromoCode
from django import forms
from crispy_forms.helper import FormHelper
from django.core.exceptions import ValidationError


class BankAccountForm(ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'account_number', 'routing_number']

        widgets = {'account_number': forms.TextInput(attrs={'placeholder': "000987654321"}),
                   'routing_number': forms.TextInput(attrs={'placeholder': "123456789"}),
                   }


class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = ['promoter', 'amount', 'image','description']

    def clean_amount(self):
        promoter = self.cleaned_data["promoter"]
        amount = self.cleaned_data["amount"]
        balance = get_balance(promoter)
        if balance < amount:
            raise ValidationError('The available balance is: %(balance)s', params={'balance': balance},)
        return amount


class PromoCodeForm(ModelForm):
    class Meta:
        model = PromoCode
        fields = ['code', 'event', 'discount_type', 'discount_value', 'max_uses', 
                 'max_uses_per_customer', 'valid_from', 'valid_until', 'description']
        
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter promo code (e.g., SAVE20)',
                'maxlength': 20
            }),
            'discount_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter discount value',
                'step': '0.01'
            }),
            'max_uses': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 100
            }),
            'max_uses_per_customer': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'value': 1
            }),
            'valid_from': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'valid_until': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal description for this promo code (optional)'
            }),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'event': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        promoter = kwargs.pop('promoter', None)
        super().__init__(*args, **kwargs)
        
        if promoter:
            # Filter events to only show events belonging to this promoter
            self.fields['event'].queryset = promoter.event_set.all()
            
        self.helper = FormHelper()
        self.helper.form_method = 'post'

    def clean_code(self):
        code = self.cleaned_data['code'].upper().strip()
        
        # Check if code already exists (excluding current instance if editing)
        existing_code = PromoCode.objects.filter(code=code)
        if self.instance.pk:
            existing_code = existing_code.exclude(pk=self.instance.pk)
            
        if existing_code.exists():
            raise ValidationError('This promo code already exists. Please choose a different code.')
            
        return code

    def clean_discount_value(self):
        discount_type = self.cleaned_data.get('discount_type')
        discount_value = self.cleaned_data.get('discount_value')
        
        if discount_value <= 0:
            raise ValidationError('Discount value must be greater than 0.')
            
        if discount_type == 'percentage' and discount_value > 100:
            raise ValidationError('Percentage discount cannot be more than 100%.')
            
        return discount_value

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_until = cleaned_data.get('valid_until')
        
        if valid_from and valid_until:
            if valid_from >= valid_until:
                raise ValidationError('Valid until date must be after valid from date.')
                
        return cleaned_data


class PartnerForm(ModelForm):
    """Form for creating/editing Business Partners and Doormen"""
    
    user = forms.ModelChoiceField(
        queryset=None,
        required=True,
        label='Select User',
        help_text='Search and select a registered user by email or name',
        widget=forms.Select(attrs={
            'class': 'form-control user-select',
            'data-live-search': 'true',
            'data-size': '8',
        }),
        empty_label="Type to search users..."
    )
    
    role = forms.ChoiceField(
        choices=[('PARTNER', 'Business Partner'), ('DOORMAN', 'Doorman')],
        required=False,
        label='Role',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select the access level for this partner'
    )
    
    class Meta:
        model = None  # Will be imported
        fields = ['user', 'role', 'event']
        
        widgets = {
            'event': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        
        labels = {
            'user': 'Select User',
            'role': 'Partner Role',
            'event': 'Assign to Event',
        }
        
        help_texts = {
            'user': 'The user must have a registered account. Search by email or name.',
            'role': 'Business Partner has full access. Doorman has limited check-in access only.',
            'event': 'Select which event this partner will have access to.',
        }
    
    def __init__(self, *args, **kwargs):
        from promoter.models import Partner
        from django.contrib.auth.models import User
        self.Meta.model = Partner
        
        promoter = kwargs.pop('promoter', None)
        role = kwargs.pop('role', None)
        self.selected_role = role
        super().__init__(*args, **kwargs)
        
        # Get all active users
        users = User.objects.filter(is_active=True).order_by('username')
        
        self.fields['user'].queryset = users
        self.fields['user'].label_from_instance = lambda obj: f"{obj.username} - {obj.get_full_name() or 'No name'}"
        
        if promoter:
            # Filter events to only show events belonging to this promoter
            from event.models import Event
            self.fields['event'].queryset = Event.objects.filter(promoter=promoter).order_by('-event_date')
        
        # If role is pre-selected (for doorman creation), hide the field and set initial value
        if role:
            self.fields['role'].initial = role
            self.fields['role'].widget = forms.HiddenInput()
            self.fields['role'].required = False
        else:
            # For business partner form, show role selection
            self.fields['role'].required = True
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
    
    def clean_user(self):
        user = self.cleaned_data.get('user')
        
        if not user:
            raise ValidationError('Please select a user.')
        
        if not user.is_active:
            raise ValidationError(f'User "{user.username}" is not active.')
        
        return user
    
    def clean_role(self):
        role = self.cleaned_data.get('role')
        
        # If role was pre-set (doorman creation), use that
        if self.selected_role:
            return self.selected_role
        
        if not role:
            raise ValidationError('Please select a role.')
        
        return role
    
    def clean(self):
        from promoter.models import Partner
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        event = cleaned_data.get('event')
        role = cleaned_data.get('role')
        
        # Use selected_role if role is hidden
        if self.selected_role:
            cleaned_data['role'] = self.selected_role
            role = self.selected_role
        
        if user and event:
            # Check if partner already exists for this event
            existing = Partner.objects.filter(email=user.username, event=event)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                existing_partner = existing.first()
                if existing_partner.disable:
                    raise ValidationError(
                        f'This user was previously assigned to this event but is currently disabled. '
                        f'Please re-enable them from the Partners list instead of creating a new assignment.'
                    )
                else:
                    raise ValidationError(
                        f'This user is already assigned to this event as {existing_partner.get_role_display()}.'
                    )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        user = self.cleaned_data.get('user')
        role = self.cleaned_data.get('role')
        
        # Set email from user
        instance.email = user.username
        instance.user = user
        
        # Set role
        if self.selected_role:
            instance.role = self.selected_role
        elif role:
            instance.role = role
        else:
            # Default to PARTNER if not specified
            instance.role = 'PARTNER'
        
        if commit:
            instance.save()
        
        return instance


class CreatePartnerWithUserForm(forms.Form):
    """
    Form for creating a NEW user and assigning them as a Partner/Doorman to an event.
    This creates the user account and the partner assignment in one step.
    """
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter last name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address'
        }),
        help_text='This will be used as the username for login. A temporary password will be sent to this email.'
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Phone Number (Optional)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter phone number'
        })
    )
    
    role = forms.ChoiceField(
        choices=[('DOORMAN', 'Doorman'), ('PARTNER', 'Business Partner')],
        required=True,
        label='Role',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Doorman: Can check-in guests at events. Business Partner: Has broader access to event management.'
    )
    
    event = forms.ModelChoiceField(
        queryset=None,
        required=True,
        label='Assign to Event',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select which event this person will have access to.'
    )
    
    def __init__(self, *args, **kwargs):
        from event.models import Event
        
        promoter = kwargs.pop('promoter', None)
        role = kwargs.pop('role', None)  # Pre-set role (for doorman-specific form)
        super().__init__(*args, **kwargs)
        
        if promoter:
            # Filter events to only show events belonging to this promoter
            self.fields['event'].queryset = Event.objects.filter(promoter=promoter).order_by('-event_date')
        
        # If role is pre-set, hide the role field
        if role:
            self.fields['role'].initial = role
            self.fields['role'].widget = forms.HiddenInput()
            self.selected_role = role
        else:
            self.selected_role = None
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
    
    def clean_email(self):
        from django.contrib.auth.models import User
        
        email = self.cleaned_data.get('email').lower().strip()
        
        # Check if email format is valid (already done by EmailField, but extra validation)
        if not email:
            raise ValidationError('Email address is required.')
        
        return email
    
    def clean(self):
        from django.contrib.auth.models import User
        from promoter.models import Partner
        
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        event = cleaned_data.get('event')
        role = cleaned_data.get('role') or self.selected_role
        
        if email and event:
            # Check if this email is already assigned to this event
            existing_partner = Partner.objects.filter(email=email, event=event).first()
            if existing_partner:
                if existing_partner.disable:
                    raise ValidationError(
                        f'This email was previously assigned to this event but is currently disabled. '
                        f'Please re-enable them from the Partners list instead.'
                    )
                else:
                    raise ValidationError(
                        f'This email is already assigned to this event as {existing_partner.get_role_display()}.'
                    )
        
        return cleaned_data
    
    def save(self):
        from django.contrib.auth.models import User
        from promoter.models import Partner
        import secrets
        import string
        
        email = self.cleaned_data['email'].lower()
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        event = self.cleaned_data['event']
        role = self.cleaned_data.get('role') or self.selected_role
        
        # Check if user already exists
        user = User.objects.filter(username=email).first()
        
        if not user:
            # Generate a random temporary password
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            
            # Create new user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=temp_password,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            
            # Send welcome email with temporary password
            self._send_welcome_email(user, temp_password, event, role)
        else:
            # Update existing user's name if provided
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.save()
        
        # Create the partner assignment
        partner = Partner.objects.create(
            email=email,
            user=user,
            role=role,
            event=event,
            disable=False
        )
        
        return partner
    
    def _send_welcome_email(self, user, temp_password, event, role):
        """Send welcome email with login credentials"""
        from django.core.mail import EmailMessage
        from django.template.loader import render_to_string
        
        try:
            role_display = 'Doorman' if role == 'DOORMAN' else 'Business Partner'
            
            subject = f"Eventlinez - You've been added as {role_display} for {event.name}"
            
            message = render_to_string('partner/email/partner_welcome.html', {
                'user': user,
                'event': event,
                'role': role_display,
                'temp_password': temp_password,
                'login_url': '/promoter/account/login/'
            })
            
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email='noreply@eventlinez.com',
                to=[user.email],
            )
            email.content_subtype = "html"
            email.send()
        except Exception as e:
            # Log the error but don't fail the creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send welcome email: {e}")
