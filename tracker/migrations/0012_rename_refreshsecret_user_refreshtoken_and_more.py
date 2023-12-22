# Generated by Django 4.2.4 on 2023-12-22 11:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0011_alter_activity_duration_alter_besteffort_time'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='refreshSecret',
            new_name='refreshToken',
        ),
        migrations.AddField(
            model_name='user',
            name='accessToken',
            field=models.CharField(default='', max_length=300),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='clientID',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='expiresAt',
            field=models.DateTimeField(default='2023-11-20 10:00'),
            preserve_default=False,
        ),
    ]