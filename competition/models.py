from django.db import models, IntegrityError, transaction
from django.db.models import Avg
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string, get_template
from django.conf import settings
import logging
import csv
import os
import datetime
import random
from decimal import Decimal

g_logger = logging.getLogger(__name__)

def current_year():
    return datetime.datetime.today().year


YEAR_CHOICES = [(r, r) for r in range(2016, current_year() + 2)]


class Sport(models.Model):
    name = models.CharField(max_length=50, unique=True)
    scoring_unit = models.CharField(max_length=50, default="point")
    match_start_verb = models.CharField(max_length=50, default="Kick Off")
    add_teams = models.FileField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        csv_file = self.add_teams
        self.add_teams = None
        super(Sport, self).save(*args, **kwargs)

        if csv_file is None:
            return

        g_logger.info("handle_teams_upload for %s csv:%s" % (self, csv_file))
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:
            try:
                row['sport'] = self
                Team(**row).save()
            except IntegrityError:
                g_logger.exception("Failed to add team")


class Team(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=3)
    sport = models.ForeignKey(Sport)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('code', 'sport',)
        unique_together = ('name', 'sport',)


class Tournament(models.Model):
    PENDING = 0
    ACTIVE = 1
    FINISHED = 2
    ARCHIVED = 3

    name = models.CharField(max_length=200, unique=True)
    participants = models.ManyToManyField(User, through="Participant")
    sport = models.ForeignKey(Sport)
    bonus = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    draw_bonus = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    late_get_bonus = models.BooleanField(default=False)
    state = models.IntegerField(default=ACTIVE,
                                choices=((PENDING, "Pending"),
                                         (ACTIVE, "Active"),
                                         (FINISHED, "finished"),
                                         (ARCHIVED, "archived")))
    winner = models.ForeignKey("Participant", null=True, blank=True, related_name='+')
    add_matches = models.FileField(null=True, blank=True)
    year = models.IntegerField(choices=YEAR_CHOICES, default=current_year)
    test_features_enabled = models.BooleanField(default=False)

    def is_closed(self):
        if self.state in [self.FINISHED, self.ARCHIVED]:
            return True
        return False

    def __str__(self):
        return self.name

    def update_table(self):
        g_logger.info("%s update_table" % self)
        for participant in self.participant_set.all():
            participant.update_score()

        for benchmark in self.benchmark_set.all():
            benchmark.update_score()

    def check_predictions(self, match):
        g_logger.info("%s: update_scores for %s", self, match)

        for participant in self.participant_set.all():
            participant.check_prediction(match)

        for benchmark in self.benchmark_set.all():
            benchmark.check_prediction(match)

        self.update_table()


    def find_team(self, name):
        try:
            return Team.objects.get(sport=self.sport, name=name)
        except Team.DoesNotExist:
            return Team.objects.get(sport=self.sport, code=name)

    def close(self, request):
        if self.state != Tournament.ACTIVE:
            return
        self.update_table()
        self.winner = Participant.objects.filter(tournament=self).order_by("score")[0]
        self.state = Tournament.FINISHED

        current_site = get_current_site(request)
        subject = "Thank you for participating in %s" % self.name

        for user in self.participants.all():
            message = render_to_string('close_email.html', {
                'user': user,
                'winner': self.winner.user.profile.get_name(),
                'winner_score': "%.2f" % self.winner.score,
                'tournament_name': self.name,
                'site_name': current_site.name,
            })
            user.profile.email_user(subject, message)

        self.save()

    def open(self, request):
        if self.state != Tournament.PENDING:
            g_logger.error("can only open tournaments that are pending")
            return
        self.state = Tournament.ACTIVE

        current_site = get_current_site(request)
        subject = "A new competition has started"
        for user in User.objects.all():
            message = render_to_string('open_email.html', {
                'user': user,
                'tournament_name': self.name,
                'site_name': current_site.name,
                'site_domain': current_site.name,
                'protocol': 'https' if request.is_secure() else 'http',
            })
            user.profile.email_user(subject, message, new_comp=True)

        self.save()

    def save(self, *args, **kwargs):
        csv_file = self.add_matches
        self.add_matches = None
        super(Tournament, self).save(*args, **kwargs)

        if not csv_file:
            return

        g_logger.info("handle_match_upload for %s csv:%s"
                      % (self, csv_file))
        reader = csv.DictReader(csv_file, delimiter=',')
        for row in reader:
            g_logger.debug("Row: %r" % row)
            if not row:
                continue
            try:
                row['tournament'] = self
                if row['home_team'] == "TBD":
                    row['home_team'] = None
                    row['home_team_winner_of'] = self.match_set.get(
                            match_id=row['home_team_winner_of'])
                else:
                    row['home_team'] = self.find_team(row['home_team'])
                    row['home_team_winner_of'] = None
                if row['away_team'] == "TBD":
                    row['away_team'] = None
                    row['away_team_winner_of'] = self.match_set.get(
                            match_id=row['away_team_winner_of'])
                else:
                    row['away_team'] = self.find_team(row['away_team'])
                    row['away_team_winner_of'] = None
                # with transaction.atomic():
                Match(**row).save()
            except (IntegrityError, ValidationError, Team.DoesNotExist, Match.DoesNotExist):
                g_logger.exception("Failed to add match")


    class Meta:
        permissions = (
            ("csv_upload", "Can add matches via CSV upload file"),
        )


class Predictor(models.Model):
    tournament = models.ForeignKey(Tournament)
    score = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)
    margin_per_match = models.DecimalField(blank=True, null=True, max_digits=6, decimal_places=2)

    def save(self, *args, **kwargs):
        created = False
        if self._state.adding:
            g_logger.info("New Predictor %s added (pre-save)" % self)
            created = True

        super(Predictor, self).save(*args, **kwargs)

        if created:
            g_logger.info("%s: Calculating prediction for each existing match", self)
            for match in Match.objects.filter(tournament=self.tournament,
                                              kick_off__lt=timezone.now(),
                                              postponed=False):
                prediction = self.predict(match)

                if match.score is not None:
                    prediction.calc_score(match.score)
                prediction.save()
            self.tournament.update_table()

    def get_name(self):
        raise NotImplementedError("%s didn't override get_name" % self.__class__)

    def predict(self, match):
        raise NotImplementedError("%s didn't override predict" % self.__class__)

    def get_predictions(self):
        raise NotImplementedError("%s didn't override get_predictions" % self.__class__)

    def get_or_create_prediction(self, match):
        raise NotImplementedError("%s didn't override get_or_create_prediction" % self.__class__)

    def get_url(self):
        return None

    def check_prediction(self, match):
        prediction = self.get_or_create_prediction(match)
        prediction.calc_score(match.score)
        prediction.save()

    def update_score(self):
        score = 0
        total_margin = 0
        num_predictions = 0
        for prediction in self.get_predictions():
            if prediction.score is not None:
                score += prediction.score
            if prediction.margin is not None:
                total_margin += prediction.margin
                num_predictions += 1
        if num_predictions == 0:
            return
        self.score = score
        self.margin_per_match = (total_margin / num_predictions)
        self.save()

    class Meta:
        abstract = True


class Participant(Predictor):
    user = models.ForeignKey(User)

    def __str__(self):
        return "%s:%s" % (self.tournament, self.user)

    def get_name(self):
        return self.user.profile.get_name()

    def predict(self, match):
        return Prediction(user=self.user, match=match, late=True)

    def get_predictions(self):
        return Prediction.objects.filter(user=self.user).filter(match__tournament=self.tournament)

    def get_or_create_prediction(self, match):
        try:
            return Prediction.objects.get(user=self.user, match=match)
        except Prediction.DoesNotExist:
            print("%s did not predict %s" % (self.user, match))
            return self.predict(match)
    
    def get_url(self):
        return "%s?user=%s" % (
                reverse('competition:predictions', args=(self.tournament.name,)),
                self.user.username)

    class Meta:
        unique_together = ('tournament', 'user',)


class Match(models.Model):
    tournament = models.ForeignKey(Tournament)
    match_id = models.IntegerField()
    kick_off = models.DateTimeField(verbose_name='Start Time')
    home_team = models.ForeignKey(Team, related_name='match_home_team', null=True, blank=True)
    home_team_winner_of = models.ForeignKey('self', blank=True, null=True, related_name='match_next_home')
    away_team = models.ForeignKey(Team, related_name='match_away_team', null=True, blank=True)
    away_team_winner_of = models.ForeignKey('self', blank=True, null=True, related_name='match_next_away')
    score = models.IntegerField(blank=True, null=True)
    postponed = models.BooleanField(blank=True, default=False)

    def __str__(self):
        s = ''
        if not self.home_team:
            s += self.home_team_winner_of.to_be_decided_str()
        else:
            s += self.home_team.name
        s += " Vs "
        if not self.away_team:
            s += self.away_team_winner_of.to_be_decided_str()
        else:
            s += self.away_team.name
        return s

    def to_be_decided_str(self):
        s = ''
        if not self.home_team:
            s += self.home_team_winner_of.to_be_decided_str()
        else:
            s += self.home_team.name
        s += "/"
        if not self.away_team:
            s += self.away_team_winner_of.to_be_decided_str()
        else:
            s += self.away_team.name
        return s

    def check_next_round_matches(self):
        if not self.score:
            return #no winner
        if self.score > 0:
            winner = self.home_team
        else:
            winner = self.away_team

        for next_round in self.match_next_home.all():
            next_round.home_team = winner
            next_round.home_team_winner_of = None
            next_round.save()

        for next_round in self.match_next_away.all():
            next_round.away_team = winner
            next_round.away_team_winner_of = None
            next_round.save()

    def has_started(self):
        if self.postponed:
            return False
        if self.kick_off > timezone.now():
            return False
        return True

    def save(self, *args, **kwargs):
        created = False
        if self._state.adding:
            g_logger.info("New Participant added (pre-save) %s" % self)
            created = True

        super(Match, self).save(*args, **kwargs)

        if not created and self.score is not None:
            self.tournament.check_predictions(self)
            g_logger.info("checking for next round matches: %s", self)
            self.check_next_round_matches()

    class Meta:
        unique_together = ('tournament', 'match_id',)
        verbose_name_plural = "matches"


class PredictionBase(models.Model):
    match = models.ForeignKey(Match)
    prediction = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    score = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)
    margin = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)

    def calc_score(self, result):
        self.margin = abs(result - self.prediction)
        if self.prediction == result:
            self.score = -self.bonus(result)
        elif (self.prediction < 0 and result < 0) or (self.prediction > 0 and result > 0):
            self.score = self.margin - self.bonus(result)
        else:
            self.score = self.margin

    def bonus(self, result):
        if result == 0: # draw 
            return self.match.tournament.bonus * self.match.tournament.draw_bonus
        return self.match.tournament.bonus

    class Meta:
        abstract = True


class Prediction(PredictionBase):
    entered = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    late = models.BooleanField(blank=True, default=False)

    def __str__(self):
        return "%s: %s" % (self.user, self.match)

    def bonus(self, result):
        if self.late and not self.match.tournament.late_get_bonus:
            return 0
        return super(Prediction, self).bonus(result)

    class Meta:
        unique_together = ('user', 'match',)


class Benchmark(Predictor):
    STATIC = 0
    MEAN = 1
    RANDOM = 2

    name = models.CharField(max_length=50)
    prediction_algorithm = models.IntegerField(choices=(
        (STATIC, "Fixed value"),
        (MEAN, "Average"),
        (RANDOM, "Random range")))
    static_value = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2)
    range_start = models.IntegerField(blank=True, null=True)
    range_end = models.IntegerField(blank=True, null=True)

    def __str__(self):
        if self.prediction_algorithm == self.STATIC:
            return "%s STATIC(%d) %s" % (self.tournament, self.static_value, self.name)
        elif self.prediction_algorithm == self.MEAN:
            return "%s MEAN %s" % (self.tournament, self.name)
        elif self.prediction_algorithm == self.RANDOM:
            return "%s RANDOM(%d, %d) %s" % (self.tournament, self.range_start, self.range_end, self.name)
        return "%s OTHER %s" % (self.tournament, self.name)


    def clean(self):
        super(Benchmark, self).clean()

        if self.prediction_algorithm == self.STATIC:
            if self.static_value is None:
                raise ValidationError('Static value is required for this prediction algorithm')
            if self.range_start is not None or self.range_end is not None:
                raise ValidationError('Range is not used with this prediction algorithm')
        elif self.prediction_algorithm == self.MEAN:
            if self.static_value is not None:
                raise ValidationError('Static value is not used with this prediction algorithm')
            if self.range_start is not None or self.range_end is not None:
                raise ValidationError('Range is not used with this prediction algorithm')
        elif self.prediction_algorithm == self.RANDOM:
            if self.static_value is not None:
                raise ValidationError('Static value is not used with this prediction algorithm')
            if self.range_start is None:
                raise ValidationError('Range start is required for this prediction algorithm')
            if self.range_end is None:
                raise ValidationError('Range end is required for this prediction algorithm')
            if self.range_start > self.range_end:
                raise ValidationError('Range start must be less than range end')

    def get_name(self):
        return self.name

    def predict(self, match):
        prediction = BenchmarkPrediction(benchmark=self, match=match)

        if self.prediction_algorithm == self.STATIC:
            prediction.prediction = self.static_value
        elif self.prediction_algorithm == self.MEAN:
            result = Prediction.objects.filter(match=match, late=False).aggregate(Avg('prediction'))
            if result['prediction__avg'] is not None:
                prediction.prediction = Decimal(result['prediction__avg'])
            else:
                prediction.prediction = 0
        elif self.prediction_algorithm == self.RANDOM:
            prediction.prediction = random.randint(self.range_start, self.range_end)
        
        return prediction

    def get_predictions(self):
        return self.benchmarkprediction_set.all()

    def get_or_create_prediction(self, match):
        try:
            return BenchmarkPrediction.objects.get(benchmark=self, match=match)
        except BenchmarkPrediction.DoesNotExist:
            print("%s did not predict %s" % (self, match))
            return self.predict(match)


class BenchmarkPrediction(PredictionBase):
    benchmark = models.ForeignKey(Benchmark)

    def __str__(self):
        return "%s: %s" % (self.benchmark, self.match)

    class Meta:
        unique_together = ('benchmark', 'match',)
