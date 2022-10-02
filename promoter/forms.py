from django.forms import ModelForm
from promoter.models import BankAccount
from django import forms

class BankAccountForm(ModelForm):
    class Meta:
        model = BankAccount
        fields = ['bank_name', 'account_number', 'routing_number']
        
        widgets = {'account_number': forms.TextInput(attrs={'placeholder':"000987654321", 'class': "form-control mb-4 col-md-4 col-lg-12 mb-0"}),
                   'routing_number': forms.TextInput(attrs={'placeholder':"123456789", 'class': "form-control col-md-4 col-lg-12 mb-0"}),
                   'bank_name': forms.TextInput(attrs={'class': "form-control mb-4 col-md-4 col-lg-12 mb-0"}),
                   }
        
         # this function will be used for the validation
    def clean(self):
        # data from the form is fetched using super function
        super(BankAccountForm, self).clean()
        # extract the username and text field from the data
        bankname = self.cleaned_data.get('bank_name')
 
        # conditions to be met for the username length
        if len(bankname) < 5:
            self._errors['username'] = self.error_class([
                'Minimum 5 characters required']) 
        # return any errors if found
        return self.cleaned_data
