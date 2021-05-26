# -*- coding: utf-8 -*-
from django.db import models


# Create your models here.

class akin(models.Model):
    user_id = models.IntegerField(null=True)
    session = models.IntegerField()
    signature = models.IntegerField()
    challenge_auth = models.CharField(max_length=63)
    timestamp = models.FloatField(null=True)
    answers = models.TextField(null=True, blank=True)
    history = models.TextField(null=True, blank=True)
    character = models.TextField(null=True)
    frontaddr = models.CharField(max_length=63, null=True)
    isNotChild = models.BooleanField(default=False)
    game_end = models.BooleanField(default=False)

    def __str__(self):
        try:
            return str(self.character).split('|')[1]
        except IndexError as e:
            return 'No character!'

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'


class profiles(models.Model):
    user_id = models.IntegerField(unique=True, verbose_name='ID персоны')
    snf = models.TextField(verbose_name='ФИО')
    img = models.CharField(max_length=511)
    how_start = models.IntegerField(verbose_name='Кол-во игр')
    how_left = models.IntegerField(verbose_name='Осталось игр')
    referals = models.TextField(null=True, blank=True, default="")
    how_referals = models.IntegerField(null=True, verbose_name='Кол-во рефералов', blank=True)
    who_referal = models.IntegerField(null=True, blank=True)
    isDonate = models.BooleanField(default=False)
    isInvite = models.BooleanField(default=False)
    timestamp_register = models.IntegerField(null=True, blank=True)
    timestamp_bonus = models.IntegerField()

    def __str__(self):
        return self.snf

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['user_id'], name='user_id_idx'),
        ]

class flood_control(models.Model):
    user_id = models.IntegerField(unique=True)
    timestamp = models.IntegerField(null=True)
    count = models.IntegerField(null=True)

    def __str__(self):
        return self.user_id


class daily_bonus(models.Model):
    user_id = models.IntegerField(null=False, blank=False, unique=False)
    timestamp = models.IntegerField(default=0)


class stats(models.Model):
    date = models.TextField(unique=True)
    js = models.TextField(null=True)
    img = models.FileField(null=True)