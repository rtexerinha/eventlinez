from django.forms import ModelForm, DateTimeField, widgets

from event.models import Category, Event


class NewCategory(ModelForm):
    class Meta:
        model = Category
        fields = ['name']


class NewEvent(ModelForm):
    event_date = DateTimeField(
        input_formats=["%Y-%m-%d %H:%M:%S"],
        widget=widgets.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    class Meta:
        model = Event
        exclude = ('slug', 'created', 'updated', 'promoter',)


class UpdateEvent(ModelForm):
    class Meta:
        model = Event
        exclude = ('slug', 'created', 'updated', 'promoter',)
