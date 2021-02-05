from django import forms
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.models import User


from customer.models import Customer
from event.models import Promoter


class SignUpFormPromoter(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(label="Email", max_length=254, help_text='eg. youremail@anyemail.com', required=True)
    address = forms.CharField(max_length=255)
    city = forms.CharField(max_length=250)
    zip = forms.CharField(max_length=11)
    social_security = forms.CharField(max_length=12, help_text='SSN information is only used for Taxes purposes.')
    phone = forms.CharField(max_length=12)

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
                "The two password fields didn’t match."
            )
        return password2

    def clean_email(self):
        email_promoter = self.cleaned_data.get("email")
        if Promoter.objects.filter(email=email_promoter).exists():
            raise ValidationError(
                "This Email is already registered.",
                code='user_existed'
            )
        return email_promoter

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
                            ssn=self.cleaned_data['social_security'],
                            phone=self.cleaned_data['phone'],
                            user=user)
        promoter.save()


class SignUpForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(label="Email", max_length=254, required=True)
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
                "The two password fields didn’t match."
            )
        return password2

    def clean_email(self):
        email_customer = self.cleaned_data.get("email")
        if Customer.objects.filter(email=email_customer).exists():
            raise ValidationError(
                "This Email has already existed.",
                code='user_existed'
            )
        return email_customer

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


class SignInPromoterForm(AuthenticationForm):
    username = UsernameField(label="Email", widget=forms.EmailInput())

    def clean(self):
        super(SignInPromoterForm, self).clean()
        try:
            promoter = self.user_cache.promoter
        except Promoter.DoesNotExist:
            raise ValidationError(
                "The user is not a Promoter",
                code='non_promoter'
            )
        return self.cleaned_data
