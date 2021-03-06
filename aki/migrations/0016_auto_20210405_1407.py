# Generated by Django 3.1.7 on 2021-04-05 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aki', '0015_akin_game_end'),
    ]

    operations = [
        migrations.CreateModel(
            name='daily_bonus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField()),
                ('timestamp', models.IntegerField(default=0)),
            ],
        ),
        migrations.AlterField(
            model_name='akin',
            name='answers',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='akin',
            name='history',
            field=models.TextField(blank=True, null=True),
        ),
    ]
