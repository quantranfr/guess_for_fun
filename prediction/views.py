from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from .models import Championship, Team, Match, Prediction, Clan, User_Clan
from datetime import datetime
import pandas as pd
import pytz, secrets

LOCKED_DELAY = 15*60 # delay after start time in seconds

@login_required
def index(request):

    context = {
        'user': request.user,
    }

    matches = Match.objects.order_by('start_time')
    predictions_user = Prediction.objects.filter(user=request.user)

    if request.method == 'POST':
        if "submit_guesses" in request.POST:
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
        elif "submit-join-clan" in request.POST:
            clan_name = request.POST['clan-name-join']
            access_code = request.POST['clan-access-code']
            context['join_clan_feedback'] = _submit_join_clan(request.user, clan_name, access_code)

        elif "submit-create-clan" in request.POST:
            clan_name = request.POST['clan-name-create']
            context['create_clan_feedback'] = _submit_create_clan(request.user, clan_name)

    user_clans = User_Clan.objects.filter(user=request.user)
    if user_clans:
        context['user_clans'] = user_clans

    display_info = []

    for match in matches:
        prediction = predictions_user.filter(match=match)
        display_info.append({
            'id': match.id,
            'start_time': match.start_time.astimezone(tz=pytz.timezone('Asia/Ho_Chi_Minh')).strftime("%a %m/%d %H:%M"),
            'team_1': match.team_1.name,
            'team_2': match.team_2.name,
            'locked': (datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))-match.start_time).total_seconds() > LOCKED_DELAY,
            'real_score_1': match.main_score_1 if match.main_score_1 else '',#  match.updated_at - match.start_time > 105*60 else None,
            'real_score_2': match.main_score_2 if match.main_score_2 else '',#updated_at - match.start_time > 105*60 else None,
            'predicted_score_1': prediction[0].main_score_1 if prediction else '',
            'predicted_score_2': prediction[0].main_score_2 if prediction else '',
        })

    context['matches'] = display_info
    return render(request, 'prediction/index.html', context)

def predict(request):
    print (request.POST)
    return HttpResponse()
    #return HttpResponse(f"{user} has just predicted.")

@permission_required('is_superuser')
def add_teams(request):
    '''
    Let users upload a file containing team info.
    Create only.
    Format: csv
    Separator: ';'
    Columns: 'name' (eg. France), 'abbr' (eg. FRA)
    '''

    template = "prediction/add_teams.html"
    context = {
        'instruction': "Accept ';' separated csv file.\
            Contains two columns 'name' and 'abbr' with header."
    }
    if request.method=='GET':
        return render(request, template, context)

    file = request.FILES['file']
    df = pd.read_csv(file, sep=';')
    res = '<pre>'
    for index, row in df.iterrows():
        name=row['name']
        abbr=row['abbr']
        res += f'Treating team {name:>30} with abbreviation: {abbr:<10}... '
        lookup = Team.objects.filter(name=name)
        if lookup:
            res += f'No action. Already exists with abbreviation: {abbr}.<br />'
        else:
            t = Team.objects.create(
                name=name,
                abbr=abbr,
            )
            t.save()
            res += 'Added.<br />'
    return HttpResponse(res+'</pre>')

@permission_required('is_superuser')
def add_matches(request):
    '''
    Let users upload a file containing match info.
    For now, create a new championship with name 'default' + timestamp
    Convert match time to UTC+UTC_DIFF_DEFAULT to store in the db.
    Create only.
    Format: csv
    Separator: ';'
    Columns: UTC_diff (eg.2);phase (eg.group);group (eg.A);start_time (eg.11-06-2021 21:00);team_1 (eg.France);team_2 (eg.Italy)
    '''

    template = "prediction/add_matches.html"
    championships = Championship.objects.all()
    context = {
        'default_championship': '' if len(championships) else 'default_' + str(int(datetime.now().timestamp())),
        'championships': championships,
        'instruction': "Accept ';' separated csv file. \
            Columns are UTC_diff (eg.2), phase (eg.group), group (eg.A), start_time (eg.11-06-2021 21:00), team_1 (eg.France), team_2 (eg.Italy).\
            Order doesn't matter."
    }
    if request.method=='GET':
        return render(request, template, context)

    if request.POST['input_championship'] != '':
        c = Championship(name=request.POST['input_championship'])
        c.save()
    else:
        c = Championship.objects.filter(name=request.POST['dropdown_championship'])[0]
    file = request.FILES['file']
    df = pd.read_csv(file, sep=';')
    df['status'] = pd.Series()
    res = '<pre>'

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
        start_time = datetime.strptime(row['start_time']+_utcdiff_to_zformat(row['UTC_diff']), '%d-%m-%Y %H:%M%z')
        res += f'Treating match {team_1.name:>20} vs. {team_2.name:<20} at {start_time}... '
        lookup = Match.objects.filter(
            team_1__name__in=(team_1, team_2),
            team_2__name__in=(team_1, team_2),
            start_time=start_time
        )

        if lookup:
            res += f'Existed. No action.<br />'
        else:
            m = Match(
                championship = c,
                phase = row['phase'],
                group = row['group'],
                team_1 = team_1,
                team_2 = team_2,
                start_time = start_time
            )
            m.save()
            res += f'Added.<br />'
    return HttpResponse(res+'</pre>')

def _utcdiff_to_zformat(utc_diff):
    '''
    convert UTC+7 to +0700 and UTC-6.5 to -0630
    '''

    return ('+' if utc_diff==abs(utc_diff) else '-') + str(int(abs(utc_diff))).zfill(2) + ('00' if utc_diff == int(utc_diff) else '30')

def _submit_join_clan(user, clan_name, access_code):
    '''
    Let a user can join a clan with his access_code.
    In: fairly clear
    Out: a message and the corresponding bootstrap class
    '''

    c = Clan.objects.filter(name=clan_name, access_code=access_code)
    if c: # the clan exists and the access code correct
        lookup = User_Clan.objects.filter(user=user, clan=c[0])
        if not lookup: # not registered before
            uc = User_Clan(user=user, clan=c[0])
            uc.save()
            return f'Congratulations! You have joined the clan {clan_name}.', 'alert-success'
        else: # already registered
            return f'No Action. You already joined the clan {clan_name}.', 'alert-warning'
    elif Clan.objects.filter(name=clan_name): # wrong access code
        return f'Wrong access code for the clan {clan_name}.', 'alert alert-danger'
    else: # no such clan
        return f'No clan {clan_name} found.', 'alert-danger'

def _submit_create_clan(user, clan_name):
    '''
    Let a user create a clan.
    In: fairly clear
    Out: a message
    '''

    if Clan.objects.filter(name=clan_name):
        return f'Clan {clan_name} already exists.', 'alert-warning'
    else:
        access_code = secrets.token_urlsafe(3)
        c = Clan(name=clan_name, access_code=access_code)
        c.save()
        uc = User_Clan(user=user, clan=c)
        uc.save()
        return f'Send this access code "{access_code}" (without quotes) to your friends so that they can join the clan {clan_name}.', 'alert-success'
