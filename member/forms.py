from django import forms
from django.contrib.auth.models import User
from .models import Profile


class NameChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class ProfileAddForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('display_name_format', 'cookie_consent',)


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user', 'dob', 'test_features_enabled')
