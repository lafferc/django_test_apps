from django import forms
from captcha.fields import ReCaptchaField
from allauth.account.forms import SignupForm
from member.models import Profile


class SignUpForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    captcha = ReCaptchaField()

    display_name_format = forms.ChoiceField(choices=Profile._meta.get_field('display_name_format').choices)
    cookie_consent = forms.ChoiceField(choices=Profile._meta.get_field('cookie_consent').choices)

    def save(self, request):
        user = super(SignUpForm, self).save(request)

        user.profile.display_name_format = self.cleaned_data['display_name_format']
        user.profile.cookie_consent = self.cleaned_data['cookie_consent']
        user.profile.save()

        return user
