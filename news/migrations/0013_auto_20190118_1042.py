# Generated by Django 2.1.5 on 2019-01-18 09:42

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0012_auto_20190118_1018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timeplace',
            name='end_time',
            field=models.TimeField(default=datetime.time(0, 0), verbose_name='End time'),
        ),
    ]
