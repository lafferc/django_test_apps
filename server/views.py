from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.loader import render_to_string, get_template
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.translation import gettext as _
import datetime
from itertools import chain

from competition.models import Tournament, Match
from member.forms import ProfileAddForm
from .forms import SignUpForm
from .tokens import account_activation_token


@login_required
def index(request):
    current_site = get_current_site(request)
    template = get_template('home.html')
    live_tournaments = Tournament.objects.filter(state=Tournament.ACTIVE)

    searchs = []
    today = datetime.date.today()
    for tourn in live_tournaments:
        if not tourn.participants.filter(pk=request.user.pk).exists():
            continue
        searchs.append(Match.objects.filter(tournament=tourn,
                                            kick_off__year=today.year,
                                            kick_off__month=today.month,
                                            kick_off__day=today.day,
                                            postponed=False))
    matches_today = sorted(
        chain(*searchs),
        key=lambda instance: instance.kick_off)

    searchs = []
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    for tourn in live_tournaments:
        if not tourn.participants.filter(pk=request.user.pk).exists():
            continue
        searchs.append(Match.objects.filter(tournament=tourn,
                                            kick_off__year=tomorrow.year,
                                            kick_off__month=tomorrow.month,
                                            kick_off__day=tomorrow.day,
                                            postponed=False))
    matches_tomorrow = sorted(
        chain(*searchs),
        key=lambda instance: instance.kick_off)

    context = {
        'site_name': current_site.name,
        'live_tournaments': live_tournaments,
        'closed_tournaments': Tournament.objects.filter(state=Tournament.FINISHED).order_by('-pk'),
        'matches_today': matches_today,
        'matches_tomorrow': matches_tomorrow,
    }
    return HttpResponse(template.render(context, request))


def signup(request):
    current_site = get_current_site(request)

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        profile_form = ProfileAddForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            user.profile.cookie_consent = profile_form.cleaned_data['cookie_consent']
            user.profile.display_name_format = profile_form.cleaned_data['display_name_format']
            user.profile.save()

            subject = 'Activate Your Account'
            message = render_to_string('registration/activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'site_name': current_site.name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http',
            })
            user.email_user(subject, message)
            return redirect('activation_sent')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        form = SignUpForm()
        profile_form = ProfileAddForm()

    context = {
        'site_name': current_site.name,
        'form': form,
        'profile_form': profile_form,
    }

    return render(request, 'registration/register.html', context)


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('index')
    else:
        return render(request, 'registration/activation_invalid.html')


def about(request):
    current_site = get_current_site(request)
    template = get_template('about.html')

    context = {
        'site_name': current_site.name,
    }
    return HttpResponse(template.render(context, request))


def gdpr(request):
    current_site = get_current_site(request)
    template = get_template('gdpr.html')

    context = {
        'site_name': current_site.name,
    }
    return HttpResponse(template.render(context, request))
