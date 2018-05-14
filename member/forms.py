from django import forms
from django.contrib.auth.models import User
from .models import Profile


class NameChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name")


class ProfileForm(forms.ModelForm):
    class Meta:
       model = Profile
       exclude = ('user', 'dob', 'test_features_enabled')
