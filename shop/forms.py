from django import forms


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
