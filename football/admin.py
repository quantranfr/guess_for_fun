from django.contrib import admin
from .models import Clan, User_Clan, Team, Match, Championship, Prediction, Prediction_Champion

admin.site.register(Clan)
admin.site.register(User_Clan)
admin.site.register(Team)
admin.site.register(Match)
admin.site.register(Championship)
admin.site.register(Prediction)
admin.site.register(Prediction_Champion)
