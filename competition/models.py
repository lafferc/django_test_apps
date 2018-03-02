from django.db import models, IntegrityError, transaction
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.contrib.sites.shortcuts import get_current_site
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string, get_template
from django.conf import settings
import logging
import csv
import os
import datetime

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
    name = models.CharField(max_length=200, unique=True)
    participants = models.ManyToManyField(User, through="Participant")
    sport = models.ForeignKey(Sport)
    bonus = models.DecimalField(max_digits=5, decimal_places=2, default=2)
    draw_bonus = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    late_get_bonus = models.BooleanField(default=False)
    state = models.IntegerField(default=1, choices=((0, "Pending"), (1, "Active"), (2, "finished"), (3, "archived")))
    winner = models.ForeignKey("Participant", null=True, blank=True, related_name='+')
    add_matches = models.FileField(null=True, blank=True)
    year = models.IntegerField(choices=YEAR_CHOICES, default=current_year)
    display_margin_per_game = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def update_table(self):
        g_logger.info("update_table")
        for participant in Participant.objects.filter(tournament=self):
            score = 0
            total_margin = 0
            num_predictions = 0
            for prediction in Prediction.objects.filter(user=participant.user).filter(match__tournament=self):
                if prediction.score is not None:
                    score += prediction.score
                if prediction.margin is not None:
                    total_margin += prediction.margin
                    num_predictions += 1
            participant.score = score
            participant.margin_per_match = (total_margin / num_predictions)
            participant.save()

    def find_team(self, name):
        try:
            return Team.objects.get(sport=self.sport, name=name)
        except Team.DoesNotExist:
            return Team.objects.get(sport=self.sport, code=name)

    def close(self, request):
        if self.state != 1:
            return
        self.update_table()
        self.winner = Participant.objects.filter(tournament=self).order_by("score")[0]
        self.state = 2

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
        if self.state != 0:
            g_logger.error("can only open tournaments that are pending")
            return
        self.state = 1

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

    class Meta:
        permissions = (
            ("csv_upload", "Can add matches via CSV upload file"),
        )

class Participant(models.Model):
    tournament = models.ForeignKey(Tournament)
    user = models.ForeignKey(User)
    score = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2);
    margin_per_match = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2);

    def __str__(self):
        return "%s" % self.user

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
            

    def check_predictions(self):
        for user in self.tournament.participants.all():
            try:
                prediction = Prediction.objects.get(user=user, match=self)
            except Prediction.DoesNotExist:
                print("%s did not predict %s" % (user, self))
                prediction = Prediction(user=user, match=self, late=True)
            prediction.calc_score(self.score)
            prediction.save()

    def check_next_round_matches(self):
        if not self.score:
            return #no winner
        if self.score > 0:
            winner = self.home_team
        else:
            winner = self.away_team
        try:
            next_round = self.match_next_home.get()
            next_round.home_team = winner
            next_round.home_team_winner_of = None
            next_round.save()
        except Match.DoesNotExist:
            pass
        try:
            next_round = self.match_next_away.get()
            next_round.away_team = winner
            next_round.away_team_winner_of = None
            next_round.save()
        except Match.DoesNotExist:
            pass

    def has_started(self):
        if self.kick_off > timezone.now():
            return False
        return True

    class Meta:
        unique_together = ('tournament', 'match_id',)


class Prediction(models.Model):
    entered = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    match = models.ForeignKey(Match)
    prediction = models.DecimalField(default=0, max_digits=5, decimal_places=2)
    score = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2);
    late = models.BooleanField(blank=True, default=False)
    margin = models.DecimalField(blank=True, null=True, max_digits=5, decimal_places=2);

    def __str__(self):
        return "%s: %s" % (self.user, self.match)

    def calc_score(self, result):
        self.margin = abs(result - self.prediction)
        if self.prediction == result:
            self.score = -self.bonus(result)
        elif (self.prediction < 0 and result < 0) or (self.prediction > 0 and result > 0):
            self.score = self.margin - self.bonus(result)
        else:
            self.score = self.margin

    def bonus(self, result):
        if self.late and not self.match.tournament.late_get_bonus:
            return 0
        if result == 0: # draw 
            return self.match.tournament.bonus * self.match.tournament.draw_bonus
        return self.match.tournament.bonus

    class Meta:
        unique_together = ('user', 'match',)


@receiver(post_save, sender=Participant, dispatch_uid="add_draw_for_matches_already_played")
def add_draws(sender, instance, created, **kwargs):
    if created:
        g_logger.info("add_draw for %s", instance)
        for match in Match.objects.filter(tournament=instance.tournament, kick_off__lt=timezone.now()):
            try:
                with transaction.atomic():
                    Prediction(user=instance.user, match=match, late=True).save()
            except IntegrityError:
                g_logger.exception("User(%s) has already predicted %s" % (instance.user, match))


@receiver(post_save, sender=Match, dispatch_uid="cal_results_for_match")
def on_match_saved(sender, instance, created, **kwargs):
    if not created and instance.score is not None:
        g_logger.info("update_scores for %s", instance)
        instance.check_predictions()
        instance.tournament.update_table()
        g_logger.info("checking for next round matches: %s", instance)
        instance.check_next_round_matches()



@receiver(post_save, sender=Sport, dispatch_uid="handle_teams_csv_upload")
def handle_team_upload(sender, instance, created, **kwargs):
    if not instance.add_teams:
        return
    g_logger.info("handle_teams_upload for %s csv:%s" % (instance, instance.add_teams))
    reader = csv.DictReader(instance.add_teams, delimiter=',')
    for row in reader:
        try:
            row['sport'] = instance
            with transaction.atomic():
               Team(**row).save()
        except IntegrityError:
            g_logger.exception("Failed to add team")
    os.remove(os.path.join(settings.MEDIA_ROOT, instance.add_teams.name))
    instance.add_teams = None
    instance.save()

@receiver(post_save, sender=Tournament, dispatch_uid="handle_matches_csv_upload")
def handle_match_upload(sender, instance, created, **kwargs):
    if not instance.add_matches:
        return
    g_logger.info("handle_match_upload for %s csv:%s" % (instance, instance.add_matches))
    reader = csv.DictReader(instance.add_matches, delimiter=',')
    for row in reader:
        g_logger.debug("Row: %r" % row)
        if not row:
            continue
        try:
            row['tournament'] = instance
            if row['home_team'] == "TBD":
                row['home_team'] = None
                row['home_team_winner_of'] = instance.match_set.get(match_id=row['home_team_winner_of'])
            else:
                row['home_team'] = instance.find_team(row['home_team'])
                row['home_team_winner_of'] = None
            if row['away_team'] == "TBD":
                row['away_team'] = None
                row['away_team_winner_of'] = instance.match_set.get(match_id=row['away_team_winner_of'])
            else:
                row['away_team'] = instance.find_team(row['away_team'])
                row['away_team_winner_of'] = None
            with transaction.atomic():
                Match(**row).save()
        except (IntegrityError, ValidationError, Team.DoesNotExist, Match.DoesNotExist):
            g_logger.exception("Failed to add match")
    os.remove(os.path.join(settings.MEDIA_ROOT, instance.add_matches.name))
    instance.add_matches = None
    instance.save()
