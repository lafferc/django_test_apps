from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.template import loader
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.db import IntegrityError

import decimal
from .models import Tournament, Match, Prediction, Participant


def tournament_from_name(name):
    try:
        return Tournament.objects.get(name=name)
    except Tournament.DoesNotExist:
        raise Http404("Tournament does not exist")

@login_required
def index(request):
    template = loader.get_template('index.html')
    current_site = get_current_site(request)
    context = {
        'site_name': current_site.name,
        'all_tournaments': Tournament.objects.all(),
        'live_tournaments': Tournament.objects.filter(state=1),
    }
    return HttpResponse(template.render(context, request))


@login_required
def submit(request, tour_name):
    tournament = tournament_from_name(tour_name)

    if tournament.state == 2:
        return redirect("competition:table", tour_name=tour_name) 

    if not tournament.participants.filter(pk=request.user.pk).exists():
        return redirect("competition:join", tour_name=tour_name) 

    fixture_list = Match.objects.filter(tournament=tournament,
                                        kick_off__gt=timezone.now()
                                        ).order_by('kick_off')

    if request.method == 'POST':
        for match in fixture_list:
            if str(match.pk) in request.POST:
                if request.POST[str(match.pk)]:
                    Prediction(user=request.user, match=match, prediction=float(request.POST[str(match.pk)])).save()

    for prediction in Prediction.objects.filter(user=request.user):
        if prediction.match in fixture_list:
            fixture_list = fixture_list.exclude(pk=prediction.match.pk)


    current_site = get_current_site(request)
    template = loader.get_template('submit.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT' : tournament,
        'fixture_list': fixture_list,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=1),
    }
    return HttpResponse(template.render(context, request))

@login_required
def predictions(request, tour_name):
    tournament = tournament_from_name(tour_name)

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        if tournament.state != 2:
            return redirect("competition:table", tour_name=tour_name)
        is_participant = False

    other_user = None
    user_score = None

    if request.method == 'POST':
        try:
            prediction_id = request.POST['prediction_id']
            prediction_prediction = float(request.POST['prediction_prediction'])
            prediction = Prediction.objects.get(pk=prediction_id,
                                                user=request.user,
                                                match__kick_off__gt=timezone.now())
            if prediction.prediction != prediction_prediction:
                prediction.prediction = prediction_prediction
                prediction.save()
        except (KeyError, ValueError, Prediction.DoesNotExist):
            pass
    elif request.GET:
        try:
            other_user = User.objects.get(username=request.GET['user'])
            if other_user == request.user:
                other_user = None
            else:
                predictions = Prediction.objects.filter(user=other_user, match__tournament=tournament, match__kick_off__lt=timezone.now()).order_by('-match__kick_off')
                other_user = other_user.profile.get_name()
        except User.DoesNotExist:
            print("User(%s) tried to look at %s's predictions but '%s' does not exist"
                  % (request.user, request.GET['user'], request.GET['user']))
        except KeyError:
            other_user = None

    if not other_user:
        if not is_participant:
            return redirect("competition:table", tour_name=tour_name)
        user_score = Participant.objects.get(user=request.user, tournament=tournament).score
        predictions = Prediction.objects.filter(user=request.user, match__tournament=tournament).order_by('-match__kick_off')

    current_site = get_current_site(request)
    template = loader.get_template('predictions.html')
    context = {
        'site_name': current_site.name,
        'other_user': other_user,
        'user_score': user_score,
        'TOURNAMENT': tournament,
        'predictions': predictions,
        'is_participant': is_participant,
        'live_tournaments': Tournament.objects.filter(state=1),
    }
    return HttpResponse(template.render(context, request))


@login_required
def table(request, tour_name):
    tournament = tournament_from_name(tour_name)

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        if tournament.state != 2:
            return redirect("competition:join", tour_name=tour_name) 
        is_participant = False

    leaderboard = []
    for participant in Participant.objects.filter(tournament=tournament).order_by('score'):
        leaderboard.append((participant.user.username,
                            participant.user.profile.get_name(),
                            participant.score,
                            participant.margin_per_match))


    current_site = get_current_site(request)
    template = loader.get_template('table.html')
    context = {
        'site_name': current_site.name,
        'leaderboard': leaderboard,
        'TOURNAMENT': tournament,
        'is_participant': is_participant,
        'live_tournaments': Tournament.objects.filter(state=1),
    }
    return HttpResponse(template.render(context, request))


@login_required
def join(request, tour_name):
    tournament = tournament_from_name(tour_name)

    if request.method == 'POST':
        try:
            Participant(user=request.user, tournament=tournament).save()
        except IntegrityError:
            pass
        return redirect('competition:submit' , tour_name=tour_name)

    current_site = get_current_site(request)
    template = loader.get_template('join.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'draw_bonus_value': tournament.bonus * tournament.draw_bonus,
        'live_tournaments': Tournament.objects.filter(state=1),
    }
    return HttpResponse(template.render(context, request))


@permission_required('competition.change_match')
def results(request, tour_name):
    tournament = tournament_from_name(tour_name)

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        is_participant = False

    fixture_list = Match.objects.filter(tournament=tournament,
                                        kick_off__lt=timezone.now(),
                                        score__isnull=True,
                                        home_team__isnull=False,
                                        away_team__isnull=False,
                                        ).order_by('kick_off')

    if request.method == 'POST':
        for match in fixture_list:
            try:
                match.score = decimal.Decimal(float(request.POST[str(match.pk)]))
                fixture_list = fixture_list.exclude(pk=match.pk)
                match.check_predictions()
                match.save()
            except (ValueError, KeyError):
                pass

    current_site = get_current_site(request)
    template = loader.get_template('match_results.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'fixture_list': fixture_list,
        'is_participant': is_participant,
        'live_tournaments': Tournament.objects.filter(state=1),
    }
    return HttpResponse(template.render(context, request))
