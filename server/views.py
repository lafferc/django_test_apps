from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.template.loader import render_to_string, get_template
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from competition.models import Tournament
from .forms import SignUpForm
from .tokens import account_activation_token


@login_required
def index(request):
    current_site = get_current_site(request)
    template = get_template('home.html')
    context = {
        'site_name': current_site.name,
        'live_tournaments': Tournament.objects.filter(state=1),
        'closed_tournaments': Tournament.objects.filter(state=2),
    }
    return HttpResponse(template.render(context, request))


def signup(request):
    if request.method == 'POST':
        user_form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
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
        user_form = SignUpForm()
    return render(request, 'registration/register.html', {'form': form})


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
