from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile

from event.models import Event


class SpecialEvents(models.Model):
    name_special_event_list = models.CharField(max_length=250, default='Special events')
    event = models.ManyToManyField(Event)
    active_list = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Special events'
        verbose_name_plural = 'Special events'

    def special_events(self):
        return ", \n".join([p.name for p in self.event.all()])


class BusinessPartner(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='partners/logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Business Partner'
        verbose_name_plural = 'Business Partners'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class EventGallery(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='gallery_photos')
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    photo = models.ImageField(
        upload_to='gallery/events/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    thumbnail = models.ImageField(upload_to='gallery/thumbnails/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    download_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Gallery Photo'
        verbose_name_plural = 'Gallery Photos'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.event.name} - {self.title or 'Photo'}"

    def increment_download_count(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def save(self, *args, **kwargs):
        # Process image on first save (when creating new instance)
        if not self.pk and self.photo:
            try:
                # Import here to avoid circular imports
                from .utils import process_gallery_image, generate_unique_filename
                
                # Generate unique filename
                unique_filename = generate_unique_filename(self.photo.name, prefix="gallery")
                self.photo.name = unique_filename
                
                # Process the image (optimize and create thumbnail)
                processed = process_gallery_image(self.photo)
                
                if processed['optimized_image']:
                    # Replace original with optimized version
                    self.photo.save(
                        processed['optimized_image'].name,
                        processed['optimized_image'],
                        save=False
                    )
                
                if processed['thumbnail'] and not self.thumbnail:
                    # Save thumbnail
                    self.thumbnail.save(
                        processed['thumbnail'].name,
                        processed['thumbnail'],
                        save=False
                    )
                    
            except Exception as e:
                # Log error but don't fail the save
                print(f"Error processing gallery image: {e}")
        
        super().save(*args, **kwargs)


class CustomerPhotoDownload(models.Model):
    customer = models.ForeignKey('customer.Customer', on_delete=models.CASCADE, related_name='photo_downloads')
    gallery_photo = models.ForeignKey(EventGallery, on_delete=models.CASCADE, related_name='customer_downloads')
    downloaded_at = models.DateTimeField(auto_now_add=True)
    download_token = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Photo Download'
        verbose_name_plural = 'Photo Downloads'
        unique_together = ['customer', 'gallery_photo']

    def __str__(self):
        return f"{self.customer.email} - {self.gallery_photo.title}"
