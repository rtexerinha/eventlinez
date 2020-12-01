from django import forms

# from event import models
# from event.models import Category, Event

'''
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category


class EventForm(forms.ModelForm):
    class Meta:
        model = Category
        exclude = ('address', 'category', 'promoter')
'''


class NewEvent(forms.Form):
    name = forms.CharField(max_length=250)
    slug = forms.SlugField(max_length=250)
    description = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-contact'}))
    unit_price = forms.DecimalField(max_digits=10,
                                    decimal_places=2)
    stock = forms.IntegerField()
    available = forms.BooleanField(initial=False)
    # category = forms.ForeignKey(Category, blank=False, on_delete=models.PROTECT)
    category = forms.CharField(max_length=250)
    event_date = forms.DateTimeField(input_formats=["%d %b %Y %H:%M:%S"],
                                     widget=forms.widgets.DateTimeInput(attrs={'type': 'datetime-local'}))
    # event_address = forms.ForeignKey(Address, blank=True, null=True, on_delete=models.PROTECT)
    # promoter = forms.ForeignKey(Promoter, on_delete=models.PROTECT)
    image = forms.ImageField()
