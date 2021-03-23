from datetimepicker import widgets
from django.forms import ModelForm, DateTimeField, TextInput
from django.contrib.auth.forms import PasswordChangeForm
from event.models import Category, Event, Promoter
from address.models import City
from django import forms


# TODO: Move this to address app
class CityForm(ModelForm):
    class Meta:
        model = City
        fields = ['name']


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class EventForm(ModelForm):
    event_date = DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        widget=widgets.DateTimeInput(attrs={'id': 'datetimepicker', 'type': 'text'}))

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
