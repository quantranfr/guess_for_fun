from django.shortcuts import render
from django.http import HttpResponse
from .models import Championship, Team, Match, Prediction
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time, pytz

LOCKED_DELAY = 15*60 # delay after start time in seconds
CHAMPIONSHIP_DEFAULT = 'Euro 2021'

def index(request):
    matches = Match.objects.order_by('start_time')
    predictions_user = Prediction.objects.filter(user=request.user)

    if request.method == 'POST':
        for match in matches:
            predicted_score_1 = request.POST[str(match.id)+'-1']
            predicted_score_2 = request.POST[str(match.id)+'-2']
            if predicted_score_1=='' or predicted_score_2=='':
                continue
            prediction = predictions_user.filter(match=match)
            if prediction:
                prediction.update(main_score_1 = predicted_score_1)
                prediction.update(main_score_2 = predicted_score_2)
            else:
                prediction = Prediction(
                    user=request.user,
                    match=match,
                    main_score_1=predicted_score_1,
                    main_score_2=predicted_score_2,
                )
                prediction.save()

    display_info = []
    for match in matches:
        prediction = predictions_user.filter(match=match)
        display_info.append({
            'id': match.id,
            'start_time': match.start_time,
            'team_1': match.team_1.name,
            'team_2': match.team_2.name,
            'locked': (datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))-match.start_time).total_seconds() > LOCKED_DELAY,
            'real_score_1': match.main_score_1 if match.main_score_1 else '',#  match.updated_at - match.start_time > 105*60 else None,
            'real_score_2': match.main_score_2 if match.main_score_2 else '',#updated_at - match.start_time > 105*60 else None,
            'predicted_score_1': prediction[0].main_score_1 if prediction else '',
            'predicted_score_2': prediction[0].main_score_2 if prediction else '',
        })

    context = {
        'user': request.user,
        'matches': display_info,
    }
    return render(request, 'prediction/index.html', context)

def predict(request):
    print (request.POST)
    return HttpResponse()
    #return HttpResponse(f"{user} has just predicted.")


def upload_team(request):
    '''
    Let users upload a file containing team info.
    Create only.
    Format: csv
    Separator: ';'
    Columns: 'name' (eg. France), 'abbr' (eg. FRA)
    '''

    template = "prediction/upload_file.html"
    context = {
        'instruction': "Accept ';' separated csv file.\
            Contains two columns 'name' and 'abbr' with header."
    }
    if request.method=='GET':
        return render(request, template, context)

    file = request.FILES['file']
    df = pd.read_csv(file, sep=';')
    res = ''
    for index, row in df.iterrows():
        name=row['name']
        abbr=row['abbr']
        lookup = Team.objects.filter(name=name)
        if lookup:
            res += f'No action. Team "{name}" exists with abbreviation: {abbr}<br />'
        else:
            _, created = Team.objects.create(
                name=name,
                abbr=abbr,
            )
            res += f'Team "{name}" created<br />' if created else f'Error with team "{name}"<br />'
    return HttpResponse(res)

def upload_match(request):
    '''
    Let users upload a file containing match info.
    Default championship provided by CHAMPIONSHIP_DEFAULT.
    Convert match time to UTC+UTC_DIFF_DEFAULT to store in the db.
    Create only.
    Format: csv
    Separator: ';'
    Columns: UTC_diff (eg.2);phase (eg.group);group (eg.A);start_time (eg.11-06-2021 21:00);team_1 (eg.France);team_2 (eg.Italy)
    '''

    template = "prediction/upload_file.html"
    context = {
        'instruction': "Accept ';' separated csv file.\
            Columns: UTC_diff (eg.2);phase (eg.group);group (eg.A);start_time (eg.11-06-2021 21:00);team_1 (eg.France);team_2 (eg.Italy)\n\
            Adding to the default championship " + CHAMPIONSHIP_DEFAULT
    }
    if request.method=='GET':
        return render(request, template, context)

    file = request.FILES['file']
    df = pd.read_csv(file, sep=';')
    df['status'] = pd.Series()
    res = '<pre>'

    championship = Championship.objects.filter(name=CHAMPIONSHIP_DEFAULT)[0]
    for index, row in df.iterrows():

        # a lot of effort here to check if a match already exists:
        # - same 2 teams
        # - same match time with accounting for time zone
        try:
            team_1 = Team.objects.filter(name=row['team_1'])[0]
            team_2 = Team.objects.filter(name=row['team_2'])[0]
        except Exception:
            res += f"Encounter problems with {row['team_1']} or {row['team_2']}. Aborted."
            return HttpResponse(res)
        utc_diff = row['UTC_diff']
        start_time = datetime.strptime(row['start_time']+utcdiff_to_zformat(row['UTC_diff']), '%d-%m-%Y %H:%M%z')#+timedelta(hours=UTC_DIFF_DEFAULT-row['UTC_diff']) # in UTC+7
        res += f'Treating match {team_1.name:>20} vs. {team_2.name:<20} at {start_time}... '
        lookup = Match.objects.filter(
            team_1__name__in=(team_1, team_2),
            team_2__name__in=(team_1, team_2),
            start_time=start_time
        )

        if np.any(lookup):
            res += f'Existed. No action.<br />'
        else:
            m = Match(
                championship = championship,
                phase = row['phase'],
                group = row['group'],
                team_1 = team_1,
                team_2 = team_2,
                start_time = start_time
            )
            m.save()
            res += f'Added.<br />'
    return HttpResponse(res+'</pre>')

def utcdiff_to_zformat(utc_diff):
    '''
    convert UTC+7 to +0700 and UTC-6.5 to -0630
    '''

    return ('+' if utc_diff==abs(utc_diff) else '-') + str(int(abs(utc_diff))).zfill(2) + ('00' if utc_diff == int(utc_diff) else '30')
