# -*- coding: utf-8 -*
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


def create_uuid(apps, schema_editor):
    Ticket = apps.get_model('ticket', 'Ticket')
    for ticket in Ticket.objects.all():
        ticket.uuid = uuid.uuid4()
        ticket.save(update_fields=['uuid'])


class Migration(migrations.Migration):

    dependencies = [
        ('ticket', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='uuid',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.RunPython(create_uuid),
        migrations.AlterField(
            model_name='ticket',
            name='uuid',
            field=models.UUIDField(unique=True)
        )
    ]
