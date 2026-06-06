from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0016_increase_cartitem_promo_code_max_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='reserved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
