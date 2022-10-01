from django.forms import ModelForm
from promoter.models import BankAccount
from django import forms

class BankAccountForm(ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'account_number', 'routing_number']
        
        widgets = {'account_number': forms.TextInput(attrs={'placeholder':"000987654321"}),
                   'routing_number': forms.TextInput(attrs={'placeholder':"123456789"})}
