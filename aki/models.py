# -*- coding: utf-8 -*-
from django.db import models


# Create your models here.

class akin(models.Model):
    user_id = models.IntegerField(null=True)
    session = models.IntegerField()
    signature = models.IntegerField()
    challenge_auth = models.CharField(max_length=63)
    timestamp = models.FloatField(null=True)
    answers = models.TextField(null=True)
    history = models.TextField(null=True)
    character = models.TextField(null=True)
    frontaddr = models.CharField(max_length=63, null=True)

    def __str__(self):
        return self.user_id

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'


class profiles(models.Model):
    user_id = models.IntegerField(unique=True, verbose_name='ID персоны')
    snf = models.TextField(verbose_name='ФИО')
    img = models.CharField(max_length=511)
    how_start = models.IntegerField(verbose_name='Кол-во игр')
    how_left = models.IntegerField(verbose_name='Осталось игр')
    referals = models.TextField(null=True)
    how_referals = models.IntegerField(null=True, verbose_name='Кол-во рефералов')
    who_referal = models.IntegerField(null=True)

    def __str__(self):
        return self.snf

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
