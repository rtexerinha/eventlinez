from django.forms import ModelForm
from promoter.models import BankAccount
from django import forms

class BankAccountForm(ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'account_number', 'routing_number']
        
        widgets = {'account_number': forms.TextInput(attrs={'data-mask':"000987654321", 'placeholder':"000987654321", 'aria-label':"000987654321"}),
                   'routing_number': forms.TextInput(attrs={'data-mask':"123456789 ", 'placeholder':"123456789", 'aria-label':"123456789"})}
        
        
        def clean_bank_name(self):
            bank_name = self.cleaned_data.get("bank_name")
            if any(char.isdigit() for char in bank_name):
                raise forms.ValidationError('bank_name')
            
        
