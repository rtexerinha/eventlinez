from django.db import models

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
