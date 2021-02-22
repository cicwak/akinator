from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('start_game/', views.start_game_without_KO_TIMEOUT),  # id=
    path('update/', views.update),  # session=&signature=&challenge_auth=&step=&ans=
    path('akin/', views.ak),
    path('last_games/', views.last_games), #
    path('gg/', views.gg),
    path('how_games/', views.how_games),  # id=
    path('post_new_user/', views.post_new_user),  # json={'id' : 0, 'snf' : '', 'img' : ''}
    path('last_10_games/', views.last_10_games),  #
    path('add_try/', views.add_try),  # id=&points=
    path('rating/', views.rating), #
    path('get_last_games_id/', views.get_last_games_id), # последние игры пользователя id=
    path('rating1/', views._rating),
    path('test/', views.test),
    path('referals/', views.referals),
    path('get_referals/', views.get_referals),
    path('ip/', views.ip),

]
