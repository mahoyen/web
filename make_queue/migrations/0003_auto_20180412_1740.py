# Generated by Django 2.0.4 on 2018-04-12 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('make_queue', '0002_auto_20180406_1800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='status',
            field=models.CharField(choices=[('R', 'Reserved'), ('F', 'Available'), ('I', 'In use'), ('O', 'Out of order'), ('M', 'Maintenance')], max_length=2),
        ),
    ]
