from datetimepicker import widgets
from django.forms import ModelForm, DateTimeField

from event.models import Category, Event
from address.models import City

# from datetimepicker.widgets import DateTimePicker


# TODO: Move this to address app
class CityForm(ModelForm):
    class Meta:
        model = City
        fields = ['name']


class NewCategory(ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class NewEvent(ModelForm):
    event_date = DateTimeField(
        input_formats=['%d/%m/%Y %H:%M'],
        widget=widgets.DateTimeInput(attrs={'id': 'datetimepicker', 'class': 'form_datetime'}))
    # event_date = DateTimeField(widget=DateTimePicker(attrs={'class': 'form_datetime'}))

    class Meta:
        model = Event
        exclude = ('slug', 'created', 'updated', 'promoter',)


class UpdateEvent(ModelForm):
    class Meta:
        model = Event
        exclude = ('slug', 'created', 'updated', 'promoter',)
