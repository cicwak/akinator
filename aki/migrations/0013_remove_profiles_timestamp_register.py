# Generated by Django 3.1.7 on 2021-04-03 11:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aki', '0012_profiles_timestamp_register'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profiles',
            name='timestamp_register',
        ),
    ]
