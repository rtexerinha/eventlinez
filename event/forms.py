from datetimepicker import widgets
from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.forms import ModelForm, DateTimeField, TextInput, ValidationError

from address.models import City
from event.models import Category
from event.models import Event
from event.models import Promoter
from event.models import Ticket


# TDO: Move this to address app
from event.models import Vendor


class CityForm(ModelForm):
    class Meta:
        model = City
        fields = ['name']


class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ['name', 'quantity', 'price', 'event']

    def __init__(self, event_id=None, *args, **kwargs):
        super(TicketForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.id:
            self.fields['event'].queryset = Event.objects.filter(id=kwargs['instance'].event_id)
            # self.fields['event'].widget.attrs['disabled'] = 'disabled'
        if event_id and type(event_id) == int:
            self.fields['event'].queryset = Event.objects.filter(id=event_id)

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if not self.instance.id:
            return quantity
        if quantity < self.instance.qty_sold():
            raise ValidationError("Ticket quantity cannot be less than quantity sold")
        return quantity


class VendorForm(ModelForm):
    class Meta:
        model = Vendor
        fields = ['first_name', 'last_name', 'email', 'phone']


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class EventForm(ModelForm):
    event_date = DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        widget=widgets.DateTimeInput(attrs={'id': 'datetimepicker', 'type': 'text'})
    )

    class Meta:
        model = Event
        exclude = ('slug', 'created', 'updated', 'promoter',)


class PromoterForm(ModelForm):
    class Meta:
        model = Promoter
        fields = ['name', 'phone', 'city', 'address', 'zip', 'ssn']
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'phone': TextInput(attrs={'class': 'form-control'}),
            'city': TextInput(attrs={'class': 'form-control'}),
            'address': TextInput(attrs={'class': 'form-control'}),
            'zip': TextInput(attrs={'class': 'form-control'}),
            'ssn': TextInput(attrs={'class': 'form-control'}),
        }


class ResetPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget = forms.PasswordInput(attrs={"class": "form-control"})
        self.fields["new_password1"].widget = forms.PasswordInput(attrs={"class": "form-control"})
        self.fields["new_password2"].widget = forms.PasswordInput(attrs={"class": "form-control"})
