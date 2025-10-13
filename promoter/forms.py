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
