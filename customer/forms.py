from django import forms
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.models import User
# from django.contrib.auth import password_validation

from customer.models import Customer
from event.models import Promoter


class SignUpFormPromoter(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(label="Email", max_length=254, help_text='eg. youremail@anyemail.com', required=True)
    address = forms.CharField(max_length=255)
    city = forms.CharField(max_length=250)
    zip = forms.CharField(max_length=11)
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=_("Your password must contain at least 8 characters, cannot password be entirely numeric."),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def clean_email(self):
        if self.cleaned_data.get("email").endswith("@test.com"):
            raise ValidationError("You cannot create a user with @test")
        return self.cleaned_data.get("email")

    def save(self):
        if not self.is_valid():
            # Todo: melhorar esse erro
            raise ValidationError("Este form não é válido")

        user = User.objects.create_user(
            self.cleaned_data["email"],
            self.cleaned_data["email"],
            self.cleaned_data["password1"],
            first_name=self.cleaned_data["name"]
        )

        user.save()
        promoter = Promoter(name=self.cleaned_data["name"],
                            email=self.cleaned_data["email"],
                            address=self.cleaned_data['address'],
                            city=self.cleaned_data['city'],
                            zip=self.cleaned_data['zip'],
                            user=user)
        promoter.save()


class SignUpForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(label="Email", max_length=254, help_text='eg. youremail@anyemail.com', required=True)
    cellphone = forms.CharField(max_length=13)
    address = forms.CharField(max_length=255)
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=_("Your password must contain at least 8 characters, cannot password be entirely numeric."),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def clean_email(self):
        if self.cleaned_data.get("email").endswith("@test.com"):
            raise ValidationError("Você não pode criar um usurio com @test")
        return self.cleaned_data.get("email")

    def save(self):
        if not self.is_valid():
            # Todo: melhorar esse erro
            raise ValidationError("Este form não é válido")

        user = User.objects.create_user(
            self.cleaned_data["email"],
            self.cleaned_data["email"],
            self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"]
        )

        user.save()
        customer = Customer(first_name=self.cleaned_data["first_name"],
                            email=self.cleaned_data["email"],
                            last_name=self.cleaned_data["last_name"],
                            cellphone=self.cleaned_data['cellphone'],
                            address=self.cleaned_data['address'],
                            user=user)
        customer.save()


class SignInForm(AuthenticationForm):
    username = UsernameField(label="Email", widget=forms.EmailInput())
