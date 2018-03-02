from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.template import loader
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from .models import Profile
from .forms import ProfileForm, NameChangeForm


@login_required
def profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)
        profile.save()

    if request.method == 'POST':
        user_form = NameChangeForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            # messages.success(request, _('Your profile was successfully updated!'))
            return redirect('member:profile')
        # else:
            # messages.error(request, _('Please correct the error below.'))
    else:
        user_form = NameChangeForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

    template = loader.get_template('profile.html')
    current_site = get_current_site(request)
    context = {
        'profile': profile,
        'site_name': current_site.name,
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return HttpResponse(template.render(context, request))


