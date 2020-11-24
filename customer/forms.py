from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.models import User

# from customer.models import Customer


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    username = forms.EmailField(label="Email", max_length=254, help_text='eg. youremail@anyemail.com')

    USERNAME_FIELD = 'email'

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'password1', 'password2')


class SignInForm(AuthenticationForm):
    username = UsernameField(label="Email", widget=forms.EmailInput())
