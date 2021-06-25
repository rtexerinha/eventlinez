from django.db import models

from event.models import Event


class SpecialEvents(models.Model):
    event = models.ManyToManyField(Event)
