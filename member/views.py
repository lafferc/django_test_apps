from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.template import loader
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site


@login_required
def profile(request):
    template = loader.get_template('profile.html')
    current_site = get_current_site(request)
    context = {
        'site_name': current_site.name,
    }
    return HttpResponse(template.render(context, request))


