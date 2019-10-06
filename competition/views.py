from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.template import loader
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.db.models import Q

import decimal
from .models import Tournament, Match, Prediction, Participant
from member.models import Competition


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
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def submit(request, tour_name):
    tournament = tournament_from_name(tour_name)

    if tournament.is_closed():
        return redirect("competition:table", tour_name=tour_name) 

    if not tournament.participants.filter(pk=request.user.pk).exists():
        return redirect("competition:join", tour_name=tour_name) 

    fixture_list = Match.objects.filter(
            Q(postponed=True) | Q(kick_off__gt=timezone.now()),
            tournament=tournament).order_by('kick_off')

    if request.method == 'POST':
        for match in fixture_list:
            try:
                Prediction(user=request.user, match=match, prediction=float(request.POST[str(match.pk)])).save()
            except (ValueError, KeyError, IntegrityError):
                continue

    for prediction in Prediction.objects.filter(user=request.user):
        if prediction.match in fixture_list:
            fixture_list = fixture_list.exclude(pk=prediction.match.pk)

    paginator = Paginator(fixture_list, 10)
    page = request.GET.get('page')
    try:
        fixture_list = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        fixture_list = paginator.page(1)

    current_site = get_current_site(request)
    template = loader.get_template('submit.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT' : tournament,
        'fixture_list': fixture_list,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))

@login_required
def predictions(request, tour_name):
    tournament = tournament_from_name(tour_name)

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        if not tournament.is_closed():
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
                predictions = Prediction.objects.filter(user=other_user, match__tournament=tournament, match__kick_off__lt=timezone.now(), match__postponed=False).order_by('-match__kick_off')
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
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def table(request, tour_name):
    tournament = tournament_from_name(tour_name)
    try:
        participant = Participant.objects.get(tournament=tournament, user=request.user)
        is_participant = True
    except Participant.DoesNotExist:
        if not tournament.is_closed():
            return redirect("competition:join", tour_name=tour_name) 
        is_participant = False

    if is_participant:
        competitions = participant.competition_set.all()
    else:
        competitions = None

    participant_list = Participant.objects.filter(tournament=tournament).order_by('score')
    paginator = Paginator(participant_list, 20)
    page = request.GET.get('page')
    try:
        participants = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        participants = paginator.page(1)

    leaderboard = []
    for participant in participants:
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
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'participants': participants,
	    'competitions': competitions,
    }
    return HttpResponse(template.render(context, request))


@login_required
def org_table(request, tour_name, org_name):
    tournament = tournament_from_name(tour_name)
    try:
        participant = Participant.objects.get(tournament=tournament, user=request.user)
        comp =  participant.competition_set.get(organisation__name=org_name)
        competitions = participant.competition_set.all().exclude(pk=comp.pk)
        competitions = [comp] + [c for c in competitions]
    except Competition.DoesNotExist:
        raise Http404("Organisation does not exist")
    except Participant.DoesNotExist:
        raise Http404()

    participant_list = comp.participants.order_by('score')
    paginator = Paginator(participant_list, 20)
    page = request.GET.get('page')
    try:
        participants = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        participants = paginator.page(1)

    current_site = get_current_site(request)
    template = loader.get_template('org_table.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'participants': participants,
	    'competitions': competitions,
    }
    return HttpResponse(template.render(context, request))


@login_required
def join(request, tour_name):
    tournament = tournament_from_name(tour_name)

    if tournament.is_closed():
        return redirect("competition:table", tour_name=tour_name) 

    if request.method == 'POST':
        try:
            Participant.objects.create(user=request.user, tournament=tournament)
        except IntegrityError:
            pass
        return redirect('competition:submit' , tour_name=tour_name)

    current_site = get_current_site(request)
    template = loader.get_template('join.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'draw_bonus_value': tournament.bonus * tournament.draw_bonus,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
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
                                        postponed=False,
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
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def rules(request, tour_name):
    tournament = tournament_from_name(tour_name)

    is_participant = True
    if not tournament.participants.filter(pk=request.user.pk).exists():
        if tournament.state == Tournament.ACTIVE:
            return redirect("competition:join", tour_name=tour_name) 
        is_participant = False

    current_site = get_current_site(request)
    template = loader.get_template('display_rules.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': tournament,
        'draw_bonus_value': tournament.bonus * tournament.draw_bonus,
        'is_participant': is_participant,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
    }
    return HttpResponse(template.render(context, request))


@login_required
def match(request, match_pk):
    try:
        match = Match.objects.get(pk=match_pk)
    except Match.DoesNotExist:
        raise Http404("Match does not exist")

    if not match.tournament.participants.filter(pk=request.user.pk).exists():
        raise Http404("User is not a Participant")

    if match.has_started():
        if match.score is not None:
            matches = match.prediction_set.all().order_by('score')
        else:
            matches = match.prediction_set.all()

        paginator = Paginator(matches, 20)
        try:
            predictions = paginator.page(request.GET.get('page'))
        except (PageNotAnInteger, EmptyPage):
            predictions = paginator.page(1)
    else:
        predictions = None

    try:
        user_prediction = match.prediction_set.get(user=request.user)
    except Prediction.DoesNotExist:
        user_prediction = None

    current_site = get_current_site(request)
    template = loader.get_template('match.html')
    context = {
        'site_name': current_site.name,
        'TOURNAMENT': match.tournament,
        'is_participant': True,
        'live_tournaments': Tournament.objects.filter(state=Tournament.ACTIVE),
        'predictions': predictions,
        'match': match,
        'prediction': user_prediction,
    }
    return HttpResponse(template.render(context, request))
