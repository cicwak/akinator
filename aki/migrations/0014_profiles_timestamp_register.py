# Generated by Django 3.1.7 on 2021-04-03 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aki', '0013_remove_profiles_timestamp_register'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiles',
            name='timestamp_register',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
