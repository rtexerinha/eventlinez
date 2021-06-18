from django import forms


class ContactForm(forms.Form):
    CHOICES = (('Event Feedback', 'Event Feedback',),
               ('Order issues', 'Order issues',),
               ('Create a new event', 'Create a new event',),)
    mail = forms.EmailField(
        required=True,
        label="",
        widget=forms.TextInput(attrs={'class': 'form-control h6-home height-17', 'placeholder': 'E-mail'})
    )
    cellphone = forms.CharField(
        required=True,
        label="",
        widget=forms.TextInput(attrs={'class': 'form-control h6-home height-17', 'placeholder': 'Cellphone'})
    )
    subject = forms.ChoiceField(
        choices=CHOICES,
        label="",
        widget=forms.Select(choices=CHOICES,
                            attrs={'class': 'form-control h6-home height-17', 'placeholder': 'Subject'})
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control h6-home height-17', 'placeholder': 'Message'}),
        label=""
    )
