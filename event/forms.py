from django import forms
from django.forms import ModelForm, ValidationError, TextInput
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone

from address.models import City
from event.models import Category, Event, Ticket
from promoter.models import Vendor, Promoter
from django.core.exceptions import ValidationError

class CityForm(ModelForm):
    class Meta:
        model = City
        fields = ["name"]


class TicketForm(ModelForm):
    class Meta:
        model = Ticket
        fields = ["name", "quantity", "price", "sold_out"]  # Removed "event" from fields

    def __init__(self, *args, **kwargs):
        event_id = kwargs.pop("event_id", None)
        super().__init__(*args, **kwargs)

        # ALWAYS remove the event field from the form to prevent HTML5 validation errors
        # The event will be set in the view when saving
        if 'event' in self.fields:
            del self.fields['event']
            print(f"✅ Event field removed from form fields")
        
        if self.instance and self.instance.pk:
            # For existing tickets, we don't need the event field
            pass
        elif event_id is not None:
            # Store the event_id for later use in the view
            self.event_id = event_id
            print(f"Form created with event_id: {event_id}")
            print(f"Form fields: {list(self.fields.keys())}")
        else:
            # If no event_id provided and not updating, we can't create a ticket
            # This shouldn't happen in normal flow since the URL requires event_id
            pass

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if not getattr(self.instance, "pk", None):
            return quantity
        if quantity < self.instance.qty_sold():
            raise ValidationError("Ticket quantity cannot be less than quantity sold")
        return quantity


class TicketUpdateForm(TicketForm):
    """Form for updating existing Ticket instances. Inherits all behaviour from TicketForm without changes."""
    pass


class VendorForm(ModelForm):
    class Meta:
        model = Vendor
        fields = ["first_name", "last_name", "email", "phone"]


class CategoryForm(ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


class EventForm(ModelForm):
    event_date = forms.DateTimeField(
        input_formats=["%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"],
        widget=forms.TextInput(
            attrs={"id": "datetimepicker", "class": "form-control"},
        ),
    )

    class Meta:
        model = Event
        exclude = ("slug", "created", "updated", "promoter", "vendors")
        widgets = {
            'is_free_event': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
    def clean_event_date(self):
        """Ensure event_date is timezone-aware"""
        event_date = self.cleaned_data.get('event_date')
        if event_date and timezone.is_naive(event_date):
            event_date = timezone.make_aware(event_date)
        return event_date


class PromoterForm(ModelForm):
    class Meta:
        model = Promoter
        fields = ["name", "phone", "city", "address", "zip", "ssn"]
        widgets = {
            "name": TextInput(attrs={"class": "form-control"}),
            "phone": TextInput(attrs={"class": "form-control"}),
            "city": TextInput(attrs={"class": "form-control"}),
            "address": TextInput(attrs={"class": "form-control"}),
            "zip": TextInput(attrs={"class": "form-control"}),
            "ssn": TextInput(attrs={"class": "form-control"}),
        }


class ResetPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget = forms.PasswordInput(attrs={"class": "form-control"})
        self.fields["new_password1"].widget = forms.PasswordInput(attrs={"class": "form-control"})
        self.fields["new_password2"].widget = forms.PasswordInput(attrs={"class": "form-control"})
