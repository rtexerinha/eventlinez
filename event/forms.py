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

        if self.instance and self.instance.pk:
            # For existing tickets, we don't need the event field
            pass
        elif event_id is not None:
            # Store the event_id for later use
            self.event_id = event_id
            print(f"Form created with event_id: {event_id}")
            print(f"Form fields: {list(self.fields.keys())}")
            print(f"Event field not included in form fields")
        else:
            # If no event_id provided, add the event field
            self.fields["event"] = forms.ModelChoiceField(
                queryset=Event.objects.all(),
                required=False,
                empty_label="Select an event"
            )

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
        input_formats=["%d/%m/%Y %H:%M"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "id": "datetimepicker"},
        ),
    )

    class Meta:
        model = Event
        exclude = ("slug", "created", "updated", "promoter", "vendors")
        
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
