from django.db import migrations


def set_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(id=1).update(domain='www.eventlinez.com', name='Eventlinez')


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_businesspartner_customerphotodownload_eventgallery'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(set_site_domain, migrations.RunPython.noop),
    ]
