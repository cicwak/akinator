# Generated by Django 3.2 on 2021-05-23 18:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aki', '0026_alter_stats_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='stats',
            name='img',
            field=models.FileField(null=True, upload_to=''),
        ),
    ]
