from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from .models import Championship, Team, Match, Prediction, Clan, User_Clan
from datetime import datetime
import pandas as pd
import pytz, secrets
import scipy.stats as ss
from collections import defaultdict

LOCKED_DELAY = 15*60 # delay after start time in seconds

@login_required
def index(request):

    context = {
        'user': request.user,
    }

    if request.method == 'POST':
        if "submit-guesses" in request.POST:
            predicted = {}
            for key in request.POST:
                if key.endswith('-1'):
                    match_id = key.rstrip('1').rstrip('-')
                    predicted[match_id] = (request.POST[key], request.POST[match_id+'-2'])
            context['submit_guesses_feedback'] = _submit_guesses(request.user, predicted)
        elif "submit-join-clan" in request.POST:
            clan_name = request.POST['clan-name-join']
            access_code = request.POST['clan-access-code']
            context['join_clan_feedback'] = _submit_join_clan(request.user, clan_name, access_code)

        elif "submit-create-clan" in request.POST:
            clan_name = request.POST['clan-name-create']
            context['create_clan_feedback'] = _submit_create_clan(request.user, clan_name)

        elif "submit-leave-clan" in request.POST:
            if 'delete-clan-id' in request.POST:
                c=Clan.objects.get(pk=request.POST['delete-clan-id'])
                c.delete()
            else:
                User_Clan.objects.filter(user=request.user, clan__id=request.POST['leave-clan-id']).delete()

    # display user's points
    context['points'] = _calculate_points(request.user)

    # display user's clans
    uclans = User_Clan.objects.filter(user=request.user)
    if uclans:
        context['uclans'] = uclans

    # display matches and user's predictions
    context['matches'] = _display_matches(request.user)

    return render(request, 'football/index.html', context)

@login_required
def clan(request, clan_id):
    '''
    Retrieve a dict <username: points>
    '''

    c = get_object_or_404(Clan, pk=clan_id)
    users = []
    for _ in User_Clan.objects.filter(clan=c):
        users.append(_.user)
    username_pts_rank = _calculate_points_and_rank(users)
    context = {
        'clan': c,
        'username_pts_rank': username_pts_rank
    }
    return render(request, 'football/clan.html', context)

@permission_required('is_superuser')
def add_teams(request):
    '''
    Let users upload a file containing team info.
    Create only.
    Format: csv
    Separator: ';'
    Columns: 'name' (eg. France), 'abbr' (eg. FRA)
    '''

    template = "football/add_teams.html"
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

    template = "football/add_matches.html"
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

def _display_matches(user):
    '''
    Get match info to display. TODO: championship matters...
    '''

    info = []
    pu = Prediction.objects.filter(user=user)
    for m in Match.objects.order_by('start_time'):
        p = pu.filter(match=m)
        info.append({
            'id': m.id,
            'start_time': m.start_time.astimezone(tz=pytz.timezone(settings.TIME_ZONE)).strftime("%a %m/%d %H:%M"),
            'team_1': m.team_1.name,
            'team_2': m.team_2.name,
            'locked': (datetime.now(pytz.timezone(settings.TIME_ZONE))-m.start_time).total_seconds() > LOCKED_DELAY,
            'real_score_1': m.main_score_1 if m.main_score_1 else '',
            'real_score_2': m.main_score_2 if m.main_score_2 else '',
            'predicted_score_1': p[0].main_score_1 if p else '',
            'predicted_score_2': p[0].main_score_2 if p else '',
        })

    return info

def _calculate_points(user):
    '''
    Get one's points. TODO: championship matters...
    '''

    pts = 0
    for p in Prediction.objects.filter(user=user):
        if p.match.main_score_1 is None: continue
        pts += _check_scoring_policy(
            p.match.main_score_1,
            p.match.main_score_2,
            p.main_score_1,
            p.main_score_2)
    return pts

def _calculate_points_and_rank(users):
    '''
    Get points for many users at the same time. TODO: championship matters...

    Suppose users' points for a clan is [1, 2, 3, 3, 3, 4, 5]
    The ranking should be               [7, 6, 3, 3, 3, 2, 1]

    Return: [(username, pts, rank)], ordered by rank
    '''

    user_pts = defaultdict(int) # <username: pts>
    for p in Prediction.objects.all():
        if p.match.main_score_1 is None: continue
        if p.user not in users: continue
        if p.user.username not in user_pts: user_pts[p.user.username]=0
        user_pts[p.user.username] += _check_scoring_policy(
            p.match.main_score_1,
            p.match.main_score_2,
            p.main_score_1,
            p.main_score_2)

    # ranking
    lp = [user_pts[u.username] for u in users] # [1, 2, 3, 3, 3, 4, 5]
    ranks = len(lp)+1-ss.rankdata(lp, method='max') # [7, 6, 3, 3, 3, 2, 1]
    rank_of_points = dict(zip(lp, ranks)) # {1:7, 2:6,...}
    res = [(u.username, user_pts[u.username], rank_of_points[user_pts[u.username]]) for u in users] # [(rank, username, pts)]
    return sorted(res, key=lambda i:i[2]) # sorted by rank

def _check_scoring_policy(s1, s2, ps1, ps2):
    '''
    s1: real score of team 1
    ps1: predicted score of team 1
    ...
    '''

    winner = 1 if s1 > s2 else 2 if s1 < s2 else 0
    winner_predicted = 1 if ps1 > ps2 else 2 if ps1 < ps2 else 0
    return 3 if winner == winner_predicted else 0

def _submit_guesses(user, predicted):
    '''
    IN: predicted: dict <match_id: (main_score_1, main_score_2)>
    OUT: Out: a message and the corresponding bootstrap class
    '''

    for match_id in predicted:
        main_score_1, main_score_2 = predicted[match_id]
        if main_score_1=='' or main_score_2=='':
            continue
        match = Match.objects.get(pk=match_id)
        prediction = Prediction.objects.filter(user=user, match=match)
        if prediction:
            prediction.update(main_score_1=main_score_1, main_score_2=main_score_2)
        else:
            prediction = Prediction(
                user=user,
                match=match,
                main_score_1=main_score_1,
                main_score_2=main_score_2,
            )
            prediction.save()
    nb_predicted = Prediction.objects.filter(user=user).count()
    nb_all = Match.objects.count()
    return f'You have predicted {nb_predicted}/{nb_all} matches.', 'alert-success'

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
    Out: a message and the corresponding bootstrap class
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

def _get_user_clan_ranking(user, clan):
    '''
    See the name
    Suppose users' scores for a clan is [1, 2, 3, 3, 3, 4, 5]
    The ranking should be [7, 6, 3, 3, 3, 2, 1]
    '''
    pass
    #return User_Clan.objects.filter(clan=clan).order_by('-points')
    #lpoints = [user.points for user in users]
    #ranks = len(lpoints)+1-ss.rankdata(lpoints, method='max')
