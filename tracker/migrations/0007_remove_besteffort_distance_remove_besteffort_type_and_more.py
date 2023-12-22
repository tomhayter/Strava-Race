# Generated by Django 4.2.4 on 2023-12-21 17:28

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0006_alter_trophy_value_alter_usermilestone_dateachieved'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='besteffort',
            name='distance',
        ),
        migrations.RemoveField(
            model_name='besteffort',
            name='type',
        ),
        migrations.AddField(
            model_name='activity',
            name='stravaID',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='besteffort',
            name='time',
            field=models.TimeField(default=datetime.time(0, 0)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='trophy',
            name='holder',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tracker.user'),
        ),
        migrations.AlterField(
            model_name='trophy',
            name='unit',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]