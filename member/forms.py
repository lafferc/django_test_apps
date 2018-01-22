from .models import Profile

class ProfileForm(forms.ModelForm):
    class Meta:
       model = Profile
       fields = ('dob',)
