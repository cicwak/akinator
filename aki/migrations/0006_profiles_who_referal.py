# Generated by Django 3.1.5 on 2021-01-24 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aki', '0005_auto_20210119_1620'),
    ]

    operations = [
        migrations.AddField(
            model_name='profiles',
            name='who_referal',
            field=models.IntegerField(null=True),
        ),
    ]
