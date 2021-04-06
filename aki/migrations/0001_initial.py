# Generated by Django 3.1.4 on 2021-01-12 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='akin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(null=True)),
                ('session', models.IntegerField()),
                ('signature', models.IntegerField()),
                ('challenge_auth', models.CharField(max_length=63)),
                ('timestamp', models.FloatField(null=True)),
                ('answers', models.TextField(null=True)),
                ('history', models.TextField(null=True)),
                ('character', models.TextField(null=True)),
                ('frontaddr', models.CharField(max_length=63, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='profiles',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.IntegerField(unique=True)),
                ('snf', models.TextField()),
                ('img', models.CharField(max_length=127)),
                ('how_start', models.IntegerField()),
                ('how_left', models.IntegerField()),
            ],
        ),
    ]
