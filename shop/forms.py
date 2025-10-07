from django import forms
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from .models import EventGallery, Event
import os


class BulkEventGalleryUploadForm(forms.Form):
    """Form for bulk uploading multiple gallery images"""
    
    event = forms.ModelChoiceField(
        queryset=Event.objects.all(),
        empty_label="Select an event",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        })
    )
    
    # Note: We handle multiple files in the admin view using request.FILES.getlist('photos')
    photos = forms.FileField(
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control',
            'id': 'bulk-photos-input'
        }),
        help_text='Select multiple images (JPEG, PNG, GIF, WebP). Maximum 10MB per image.',
        required=False  # We'll validate in clean method
    )
    
    title_prefix = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Optional title prefix (e.g., "Event Highlights")'
        }),
        help_text='If provided, each photo will get this prefix + number (e.g., "Event Highlights 1")'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional description for all uploaded photos'
        }),
        required=False,
        help_text='This description will be applied to all uploaded photos'
    )
    
    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Mark all uploaded photos as featured'
    )
    
    is_public = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text='Make all uploaded photos public'
    )
    
    def clean_photos(self):
        files = self.files.getlist('photos')
        
        if not files:
            raise ValidationError('Please select at least one image.')
        
        if len(files) > 50:  # Reasonable limit
            raise ValidationError('You can upload maximum 50 images at once.')
        
        for file in files:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise ValidationError(f'File "{file.name}" is too large. Maximum size is 10MB.')
            
            # Check file extension
            ext = os.path.splitext(file.name)[1].lower()
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if ext not in allowed_extensions:
                raise ValidationError(f'File "{file.name}" has an invalid extension. Allowed: {", ".join(allowed_extensions)}')
            
            # Check if it's actually an image
            try:
                width, height = get_image_dimensions(file)
                if width is None or height is None:
                    raise ValidationError(f'File "{file.name}" is not a valid image.')
            except Exception:
                raise ValidationError(f'File "{file.name}" could not be processed as an image.')
        
        return files


class EventGalleryForm(forms.ModelForm):
    """Enhanced form for single gallery photo upload"""
    
    class Meta:
        model = EventGallery
        fields = ['event', 'title', 'description', 'photo', 'is_featured', 'is_public']
        widgets = {
            'event': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        
        if photo:
            # Check file size (10MB limit)
            if photo.size > 10 * 1024 * 1024:
                raise ValidationError('Image file is too large. Maximum size is 10MB.')
            
            # Check if it's actually an image
            try:
                width, height = get_image_dimensions(photo)
                if width is None or height is None:
                    raise ValidationError('File is not a valid image.')
                
                # Optionally check minimum dimensions
                if width < 200 or height < 200:
                    raise ValidationError('Image is too small. Minimum size is 200x200 pixels.')
                    
            except Exception:
                raise ValidationError('File could not be processed as an image.')
        
        return photo


class ContactForm(forms.Form):
    """Contact form with validation"""
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'What is this about?',
            'required': True
        }),
        label='Subject'
    )
    
    mail = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com',
            'required': True
        }),
        label='Email Address'
    )
    
    cellphone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+1 (555) 123-4567',
        }),
        label='Phone Number (Optional)'
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Tell us more about your inquiry...',
            'required': True
        }),
        label='Message'
    )