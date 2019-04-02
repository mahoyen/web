# Generated by Django 2.1.5 on 2019-02-13 19:54

from django.db import migrations, models
import make_queue.fields


class Migration(migrations.Migration):

    dependencies = [
        ('make_queue', '0008_auto_20181103_1524'),
    ]

    operations = [
        migrations.AlterField(
            model_name='machine',
            name='location',
            field=models.CharField(max_length=40, verbose_name='Location'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='location_url',
            field=models.URLField(verbose_name='Location URL'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='machine_model',
            field=models.CharField(max_length=40, verbose_name='Machine model'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='machine_type',
            field=make_queue.fields.MachineTypeField(choices=[(1, '3D-printers'), (2, 'Sewing machines')], null=True, verbose_name='Machine type'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='name',
            field=models.CharField(max_length=30, unique=True, verbose_name='Name'),
        ),
        migrations.AlterField(
            model_name='machine',
            name='status',
            field=models.CharField(choices=[('R', 'Reserved'), ('F', 'Available'), ('I', 'In use'), ('O', 'Out of order'), ('M', 'Maintenance')], default="F", max_length=2, verbose_name='Status'),
        ),
    ]