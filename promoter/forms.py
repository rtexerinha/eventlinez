from django.forms import ModelForm
from promoter.models import BankAccount


class BankAccountForm(ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'last4', 'routing_number']