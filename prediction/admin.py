from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Clan, Team, Match, Championship, User_Championship, Prediction

admin.site.register(User, UserAdmin)
admin.site.register(Clan)
admin.site.register(Team)
admin.site.register(Match)
admin.site.register(Championship)
admin.site.register(User_Championship)
admin.site.register(Prediction)
