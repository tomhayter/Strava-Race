# Generated by Django 4.2.4 on 2023-12-21 18:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0007_remove_besteffort_distance_remove_besteffort_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='duration',
            field=models.DateTimeField(),
        ),
    ]
