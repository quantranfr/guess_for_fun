from django.urls import path

from . import views

app_name = 'football'
urlpatterns = [
    path('', views.index, name='index'),
    path('clan/<int:clan_id>', views.clan, name='clan'),
    path('add-teams', views.add_teams, name='add_teams'),
    path('add-matches', views.add_matches, name='add_matches'),
]
