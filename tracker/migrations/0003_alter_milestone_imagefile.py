# Generated by Django 4.2.4 on 2023-12-20 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_rename_name_user_fullname_user_firstname_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='milestone',
            name='imageFile',
            field=models.CharField(max_length=100, null=True),
        ),
    ]