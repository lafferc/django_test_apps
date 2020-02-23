from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import loader
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.utils.translation import gettext as _
from .models import Profile, Ticket, Competition
from .forms import ProfileEditForm, NameChangeForm
from competition.models import Participant
import logging

g_logger = logging.getLogger(__name__)


@login_required
def profile(request):
    if request.method == 'POST':
        user_form = NameChangeForm(request.POST, instance=request.user)
        profile_form = ProfileEditForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Your profile was successfully updated!'))
            return redirect('member:profile')
        else:
            messages.error(request, _('Please correct the error below.'))
    else:
        user_form = NameChangeForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)

    template = loader.get_template('profile.html')
    current_site = get_current_site(request)
    context = {
        'profile': request.user.profile,
        'site_name': current_site.name,
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return HttpResponse(template.render(context, request))


@login_required
def use_token(request):
    if request.method == 'POST':
        try:
            token = request.POST['token'].upper()
            ticket = Ticket.objects.get(used=False, token=token)
            ticket.used = True
            g_logger.debug("Found ticket for token:%s" % token)
            tourn = ticket.competition.tournament
            try:
                participant = Participant.objects.get(user=request.user,
                                                      tournament=tourn)
            except Participant.DoesNotExist:
                participant = Participant(user=request.user,
                                          tournament=tourn)
                participant.save()
            ticket.competition.participants.add(participant)
            ticket.save()
            return redirect('competition:org_table',
                            tour_name=tourn.name,
                            org_name=ticket.competition.organisation.name)
        except Exception:
            g_logger.exception("Failed to process token")

    template = loader.get_template('token.html')
    current_site = get_current_site(request)
    context = {
        'site_name': current_site.name,
    }
    return HttpResponse(template.render(context, request))


@user_passes_test(lambda user: user.is_superuser)
def announcement(request):
    current_site = get_current_site(request)
    if request.method == 'POST':
        subject = ""
        body = ""
        try:
            subject = request.POST["subject"]
            body = request.POST["message"]
            test_flag = request.POST["test_email"]  == "true"
        except KeyError:
            test_flag = False

        if not len(body) or not len(subject):
            raise Http404("Subject or body missing")

        if test_flag:
            user_list = [request.user]
        else:
            user_list = User.objects.all()

        sent_to = 0
        for user in user_list:
            message = loader.render_to_string('announcement_email.html', {
                'user': user,
                'body': body,
                'site_name': current_site.name,
                'site_domain': current_site.name,
                'protocol': 'https' if request.is_secure() else 'http',
            })
            if user.profile.email_user(subject, message):
                sent_to += 1

        template = loader.get_template('announcement_sent.html')
        context = {
            'site_name': current_site.name,
            'user_list_len': sent_to,
        }

        return HttpResponse(template.render(context, request))

    template = loader.get_template('announcement.html')
    context = {
        'site_name': current_site.name,
    }

    return HttpResponse(template.render(context, request))


@permission_required('competition.change_match')
def print_tickets(request, comp_pk):
    current_site = get_current_site(request)

    comp = get_object_or_404(Competition, pk=comp_pk)

    tickets = comp.ticket_set.filter(used=False)

    if not tickets:
        raise Http404("Competition has no tickets")

    template = loader.get_template('tickets.html')
    context = {
        'site_name': current_site.name,
        'comp': comp,
        'tickets': tickets,
    }

    return HttpResponse(template.render(context, request))
