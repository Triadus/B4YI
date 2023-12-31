# Generated by Django 4.2.2 on 2023-08-02 16:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0019_wallet_percentage_of_total_balance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wallet',
            name='percentage_of_total_balance',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True,
                                      verbose_name='% of total balance'),
        ),
    ]
