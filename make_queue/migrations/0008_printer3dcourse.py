# Generated by Django 2.1 on 2018-10-02 17:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('make_queue', '0007_auto_20180914_1306'),
    ]

    operations = [
        migrations.CreateModel(
            name='Printer3DCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('date', models.DateField()),
                ('card_number', models.IntegerField(null=True)),
                ('name', models.CharField(max_length=256)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
