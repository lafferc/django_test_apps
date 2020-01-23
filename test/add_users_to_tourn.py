from competition.models import *
from django.contrib.auth.models import User

usernames = ["Alice", "Bob", "Eve"]

tourn = Tournament.objects.get(pk=11)

for name in usernames:
    user = User.objects.get(username=name)
    Participant.objects.create(tournament=tourn, user=user)

