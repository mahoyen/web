# Generated by Django 2.1.7 on 2019-04-02 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_auto_20190312_1901'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='consumeable',
            field=models.BooleanField(default=False),
        ),
    ]
