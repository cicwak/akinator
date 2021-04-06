from django.urls import path, include

from . import views

urlpatterns = [
    path('start_game/', views.start_game_ip),  # id=
    path('start_game_ip/', views.start_game_ip),
    path('update/', views.update),  # session=&signature=&challenge_auth=&step=&ans=
    path('last_games/', views.last_games),
    path('how_games/', views.how_games),  # id=
    path('post_new_user/', views.post_new_user),  # json={'id' : 0, 'snf' : '', 'img' : ''}
    path('last_10_games/', views.last_10_games),  #
    path('add_try/', views.add_try),  # id=&points=
    path('rating/', views.rating),
    path('get_last_games_id/', views.get_last_games_id),  # последние игры пользователя id=
    path('referals/', views.referals),
    path('get_referals/', views.get_referals), #
    path('daily_rating/', views.daily_rating),
    path('add_donate/', views.add_donate), #
    path('remove_donate/', views.remove_donate), #
    path('test_headers/', views.test_headers),
    path('ip/', views.ip),
    path('rating_beetween_friends/', views.rating_beetween_friends),
    path('get_daily_bonus/', views.get_attemp),
]