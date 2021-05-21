# Generated by Django 3.2 on 2021-05-20 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aki', '0021_merge_20210520_2010'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='profiles',
            index=models.Index(fields=['user_id'], name='aki_profile_user_id_f4b1ee_idx'),
        ),
        migrations.AddIndex(
            model_name='profiles',
            index=models.Index(fields=['user_id'], name='user_id_idx'),
        ),
    ]
