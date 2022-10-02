from django.forms import ModelForm
from promoter.models import BankAccount
from django import forms
from crispy_forms.helper import FormHelper

class BankAccountForm(ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'account_number', 'routing_number']
        
        widgets = {'account_number': forms.TextInput(attrs={'placeholder':"000987654321"}),
                   'routing_number': forms.TextInput(attrs={'placeholder':"123456789"}),
                   }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_class = 'h5-promoter-modal'
        
