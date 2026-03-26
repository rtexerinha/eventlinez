from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0015_remove_session_timer_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='promo_code',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
