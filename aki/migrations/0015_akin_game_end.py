# Generated by Django 3.1.7 on 2021-04-03 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aki', '0014_profiles_timestamp_register'),
    ]

    operations = [
        migrations.AddField(
            model_name='akin',
            name='game_end',
            field=models.BooleanField(default=False),
        ),
    ]
