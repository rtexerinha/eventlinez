from dataclasses import fields
from django.forms import ModelForm
from promoter.models import BankAccount, Payment, get_balance
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_class = 'h5-promoter-modal'


class PaymentForm(ModelForm):
    class Meta:
        model = Payment
        fields = '__all__'

    def clean_amount(self):
        promoter = self.cleaned_data["promoter"]
        amount = self.cleaned_data["amount"]
        balance = get_balance(promoter)
        if balance < amount:
            raise ValidationError('The available balance is: %(balance)s', params={'balance': balance},)
        return 0
