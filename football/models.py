from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Team(models.Model):
    abbr = models.CharField(default=None, max_length=10)
    name = models.CharField(default=None, max_length=200)

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
    phase = models.CharField(default=None, max_length=200)
    group = models.CharField(default=None, max_length=200)
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
    access_code = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class User_Clan(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    clan = models.ForeignKey(
        Clan,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.user} has joined {self.clan}'

class Prediction(models.Model):
    user = models.ForeignKey(
        User,
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

    def __str__(self):
        return f'{self.user}\t{self.match}\t{self.main_score_1}-{self.main_score_2}'


class Prediction_Champion(models.Model):
    championship = models.ForeignKey(
        Championship,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f'{self.championship}\t{self.user}\t{self.team}'
