from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from datetime import datetime

class Team(models.Model):
    id = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=200)
    group = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return self.name

class Championship(models.Model):
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name
    
class Match(models.Model):
    championship = models.ForeignKey(
        Championship,
        null=True,
        on_delete=models.SET_NULL
    )
    team_1 = models.ForeignKey(
        Team,
        related_name='team_1',
        on_delete=models.CASCADE,
    )
    team_2 = models.ForeignKey(
        Team,
        related_name='team_2',
        on_delete=models.CASCADE,
    )
    start_time = models.DateTimeField()
    main_score_1 = models.IntegerField(default=None, null=True, blank=True)
    main_score_2 = models.IntegerField(default=None, null=True, blank=True)
    penalty_score_1 = models.IntegerField(default=None, null=True, blank=True)
    penalty_score_2 = models.IntegerField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.team_1.name} vs. {self.team_2.name} at {self.start_time}'

class Clan(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class User(AbstractUser):
    clan = models.ForeignKey(
        Clan,
        null=True,
        on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.email


class User_Championship(models.Model):
    championship = models.ForeignKey(
        Championship,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.user.email + ': ' + self.championship.name


class Prediction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE,
    )
    main_score_1 = models.IntegerField(default=None, null=True, blank=True)
    main_score_2 = models.IntegerField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
