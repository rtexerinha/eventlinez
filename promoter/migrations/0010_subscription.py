# Generated migration for Subscription model

from django.db import migrations, models
import django.db.models.deletion
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('promoter', '0009_auto_20250829_0919'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan', models.CharField(choices=[('basic', 'Basic Plan'), ('pro', 'Promoter Pro'), ('enterprise', 'Enterprise')], default='pro', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('cancelled', 'Cancelled'), ('expired', 'Expired'), ('suspended', 'Suspended')], default='active', max_length=20)),
                ('monthly_fee', models.DecimalField(decimal_places=2, default=Decimal('29.99'), max_digits=10)),
                ('next_billing_date', models.DateTimeField()),
                ('last_billing_date', models.DateTimeField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('cancelled_date', models.DateTimeField(blank=True, null=True)),
                ('expires_date', models.DateTimeField(blank=True, null=True)),
                ('cancellation_reason', models.CharField(blank=True, choices=[('too_expensive', 'Too expensive'), ('not_using_features', 'Not using enough features'), ('found_alternative', 'Found a better alternative'), ('technical_issues', 'Technical issues'), ('business_closure', 'Closing business'), ('other', 'Other')], max_length=50, null=True)),
                ('cancellation_feedback', models.TextField(blank=True, null=True)),
                ('payment_method', models.CharField(default='•••• •••• •••• 4242', max_length=100)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=100, null=True)),
                ('promoter', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='event.promoter')),
            ],
            options={
                'verbose_name': 'Subscription',
                'verbose_name_plural': 'Subscriptions',
                'ordering': ['-created_date'],
            },
        ),
    ]