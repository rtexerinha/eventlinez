from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    username = forms.EmailField(label="Email", max_length=254, help_text='eg. youremail@anyemail.com')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password1', 'password2')


class SignInForm(AuthenticationForm):
    username = UsernameField(label="Email", widget=forms.EmailInput())


class ContactForm(forms.Form):
    # name = forms.CharField(required=True,
    #                      label="Name",
    #                       widget=forms.TextInput(attrs={'class': 'form-contact namef'}))
    mail = forms.EmailField(required=True,
                            label="Email",
                            widget=forms.TextInput(attrs={'class': 'form-contact'}))
    cellphone = forms.CharField(required=True,
                                label="cellphone",
                                widget=forms.TextInput(attrs={'class': 'form-contact'}))
    CHOICES = (('Event Feedback', 'Event Feedback',),
               ('Order issues', 'Order issues',),
               ('Create a new event', 'Create a new event',),)
    subject = forms.ChoiceField(choices=CHOICES,
                                widget=forms.Select(choices=CHOICES, attrs={'class': 'select-form-contact'}))

    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-contact'}),
        label="Message"
    )
