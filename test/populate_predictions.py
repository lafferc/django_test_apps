from competition.models import *
from django.db import IntegrityError
import random

MIN = -40
MAX = 40

tourn = Tournament.objects.get(pk=11)

matches = tourn.match_set.all()

for part in tourn.participant_set.exclude(user__is_staff=True):
    for match in matches:
        try:
            Prediction.objects.create(user=part.user, match=match, prediction=random.randint(MIN, MAX))
        except IntegrityError:
            continue



