# -*- coding: utf-8 -*-
from django.contrib import admin

# Register your models here.

from .models import akin, profiles, daily_bonus


class akinAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'session', 'signature', 'challenge_auth')
    search_fields = ('user_id', 'challenge_auth')


admin.site.register(akin, akinAdmin)


class profilesAdmin(admin.ModelAdmin):
    list_display = ('snf', 'user_id', 'how_start', 'how_left', 'how_referals')
    list_display_links = ('snf', 'user_id')
    search_fields = ('snf', 'user_id')


admin.site.register(profiles, profilesAdmin)

class dailyAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'timestamp')

admin.site.register(daily_bonus, dailyAdmin)