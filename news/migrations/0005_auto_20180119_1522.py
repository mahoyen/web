# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-01-19 15:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0004_auto_20180113_0641'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Bilde'),
        ),
    ]