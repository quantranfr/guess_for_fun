from django.urls import path

from . import views

app_name = 'prediction'
urlpatterns = [
    path('', views.index, name='index'),
    path('upload-team', views.upload_team, name='upload_team'),
    path('upload-match', views.upload_match, name='upload_match'),
]
