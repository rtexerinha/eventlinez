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
    days = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        required=False,
        label='Number of Days',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'max': 10,
            'value': 1,
        }),
        help_text='Set to 3 for a Full Pass (3-day ticket). Each day will be linked to a different event.'
    )

    class Meta:
        model = Ticket
        fields = ["name", "quantity", "price", "sold_out", "days"]

    def __init__(self, *args, **kwargs):
        event_id = kwargs.pop("event_id", None)
        promoter = kwargs.pop("promoter", None)
        super().__init__(*args, **kwargs)

        if 'event' in self.fields:
            del self.fields['event']

        self.event_id = event_id
        self.promoter = promoter

        # Build dynamic full-pass event fields based on current days value
        days_value = 1
        if self.instance and self.instance.pk:
            days_value = self.instance.days or 1
        elif self.data.get('days'):
            try:
                days_value = int(self.data.get('days'))
            except (ValueError, TypeError):
                days_value = 1

        # Determine which events the promoter owns for the dropdowns
        from event.models import Event as EventModel
        if promoter:
            event_qs = EventModel.objects.filter(promoter=promoter).order_by('-event_date')
        else:
            event_qs = EventModel.objects.all().order_by('-event_date')

        for day in range(1, days_value + 1):
            field_name = f'full_pass_event_day_{day}'
            initial_event = None
            if self.instance and self.instance.pk:
                fp = self.instance.full_pass_events.filter(day_number=day).first()
                if fp:
                    initial_event = fp.event_id
            self.fields[field_name] = forms.ModelChoiceField(
                queryset=event_qs,
                required=(days_value > 1),
                label=f'Day {day} Event',
                initial=initial_event,
                widget=forms.Select(attrs={'class': 'form-control full-pass-event-select'}),
                help_text=f'Select the event that will be held on Day {day} of this Full Pass.'
            )
            if initial_event:
                self.initial[field_name] = initial_event

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if not getattr(self.instance, "pk", None):
            return quantity
        if quantity < self.instance.qty_sold():
            raise ValidationError("Ticket quantity cannot be less than quantity sold")
        return quantity

    def clean_days(self):
        days = self.cleaned_data.get('days')
        return days if days else 1

    @property
    def full_pass_event_fields(self):
        """Returns only the dynamic full-pass-event fields for use in the template."""
        return [(name, field) for name, field in self.fields.items() if name.startswith('full_pass_event_day_')]


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
