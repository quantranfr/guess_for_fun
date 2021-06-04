from django.shortcuts import render
from django.http import HttpResponse
from .models import Match, Prediction
from datetime import datetime

LOCKED_DELAY = 15*60 # delay after start time in seconds

def index(request):
    matches = Match.objects.order_by('start_time')
    predictions = Prediction.objects.filter(user=request.user)
    display_info = []
    for match in matches:
        prediction = predictions.filter(match=match)
        display_info.append({
            'id': match.id,
            'start_time': match.start_time,
            'team_1': match.team_1.name,
            'team_2': match.team_2.name,
            'locked': (datetime.now()-match.start_time).total_seconds() > LOCKED_DELAY,
            'real_score_1': match.main_score_1 if match.main_score_1 else '',#  match.updated_at - match.start_time > 105*60 else None,
            'real_score_2': match.main_score_2 if match.main_score_2 else '',#updated_at - match.start_time > 105*60 else None,
            'predicted_score_1': prediction.main_score_1 if prediction else '', 
            'predicted_score_2': prediction.main_score_2 if prediction else '', 
        })
        prediction = predictions.filter(match=match)
    print(display_info)
    context = {
        'user': request.user,
        'matches': display_info,
    }
    return render(request, 'prediction/index.html', context)

def predict(request, user):
    return HttpResponse(f"{user} has just predicted.")
