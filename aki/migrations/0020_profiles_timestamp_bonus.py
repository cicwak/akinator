# Generated by Django 3.1.7 on 2021-04-05 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aki', '0019_remove_profiles_timestamp_bonus'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiles',
            name='timestamp_bonus',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
