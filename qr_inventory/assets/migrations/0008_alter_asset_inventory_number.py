# Generated by Django 5.0.3 on 2025-06-17 04:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0007_alter_asset_inventory_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='inventory_number',
            field=models.CharField(max_length=100, unique=True, verbose_name='Инвентарный номер'),
        ),
    ]
