import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta


class TicketShareToken(models.Model):
    """One-time share token so a customer can give someone else their QR without login."""
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)
    ticket = models.ForeignKey('ticket.Ticket', on_delete=models.CASCADE, related_name='share_tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    revoked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.revoked and timezone.now() < self.expires_at

    def __str__(self):
        return f"ShareToken {self.token} → Ticket #{self.ticket_id}"
