from datetimepicker import widgets
from django.forms import ModelForm, DateTimeField

from event.models import Category, Event
from address.models import City


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
