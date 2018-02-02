from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.template import loader
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from .models import Profile
from .forms import ProfileForm


@login_required
def profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
        profile.save()

    form = ProfileForm()
    template = loader.get_template('profile.html')
    current_site = get_current_site(request)
    context = {
        'profile': profile,
        'site_name': current_site.name,
        'form': form,
    }
    return HttpResponse(template.render(context, request))


