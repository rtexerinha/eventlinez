
from django import forms


class AddItemToCardForm(forms.Form):
    promo_code = forms.CharField(label="Promo Code", max_length=8)
