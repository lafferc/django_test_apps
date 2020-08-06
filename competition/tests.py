from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import timezone

import datetime
import pytz
import unittest

from .models import Sport, Tournament, Participant
from .models import Benchmark, Team, Match

class CompetitionViewLoggedOutTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_index(self):
        url = reverse('competition:index')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_predictions(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_table(self):
        url = reverse('competition:table', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_org_table(self):
        url = reverse('competition:org_table', kwargs={'tour_name':'tourn', 'org_name': 'org'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_join(self):
        url = reverse('competition:join', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_results(self):
        url = reverse('competition:results', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_rules(self):
        url = reverse('competition:rules', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_match(self):
        url = reverse('competition:match', kwargs={'match_pk':1})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_benchmark_table(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_benchmark(self):
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': 1})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)


class CompetitionViewNotParticipantTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        #print("setUpTestData: Run once to set up non-modified data for all class methods.")
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()
        test_user2 = User.objects.create_user(username='testuser2', password='test123')
        test_user2.save()

        sport = Sport.objects.create(name='sport')
        for state, name in Tournament._meta.get_field('state').choices:
            # print("creating %s_tourn" % name.lower())
            Tournament.objects.create(name='%s_tourn' % name.lower(), sport=sport, state=state)

    def setUp(self):
        #print("setUp: Run once for every test method to setup clean data.")
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def tearDown(self):
        #print("tearDown: Run after every test method")
        pass

    def test_index(self):
        response = self.client.get(reverse('competition:index'))

        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(response, 'index.html')

    def test_submit_pending(self):
        url = reverse('competition:submit', kwargs={'tour_name':'pending_tourn'})
        join_url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, join_url)

    def test_submit_active(self):
        url = reverse('competition:submit', kwargs={'tour_name':'active_tourn'})
        join_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, join_url)

    def test_submit_finished(self):
        url = reverse('competition:submit', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_submit_archived(self):
        url = reverse('competition:submit', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_pending(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_predictions_active(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_predictions_finished(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_archived(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_pending(self):
        url = reverse('competition:table', kwargs={'tour_name':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_active(self):
        url = reverse('competition:table', kwargs={'tour_name':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_table_finished(self):
        url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_archived(self):
        url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_join_pending(self):
        url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='pending_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='pending_tourn'))
        self.assertEqual(count_after, count_before + 1)

        r_url = reverse('competition:submit', kwargs={'tour_name':'pending_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_active(self):
        url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='active_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='active_tourn'))
        self.assertEqual(count_after, count_before + 1)

        r_url = reverse('competition:submit', kwargs={'tour_name':'active_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_finished(self):
        url = reverse('competition:join', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)
        count_before = len(Participant.objects.filter(tournament__name='finished_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='finished_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_join_archived(self):
        url = reverse('competition:join', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

        count_before = len(Participant.objects.filter(tournament__name='archived_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='archived_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_results_pending(self):
        url = reverse('competition:results', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_active(self):
        url = reverse('competition:results', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_finished(self):
        url = reverse('competition:results', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_archived(self):
        url = reverse('competition:results', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_rules_pending(self):
        url = reverse('competition:rules', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_rules_active(self):
        url = reverse('competition:rules', kwargs={'tour_name':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_rules_finished(self):
        url = reverse('competition:rules', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_archived(self):
        url = reverse('competition:rules', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

#     def test_match_pending(self):
#     def test_match_active(self):
#     def test_match_finished(self):
#     def test_match_archived(self):
# 
    def test_benchmark_table_pending(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'pending_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_active(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'active_tourn'})
        r_url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_finished(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)

    def test_benchmark_table_archived(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, r_url)


class CompetitionViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        #print("setUpTestData: Run once to set up non-modified data for all class methods.")
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()
        test_user2 = User.objects.create_user(username='testuser2', password='test123')
        test_user2.save()

        sport = Sport.objects.create(name='sport')
        team_a = Team.objects.create(name='team A', code='AAA', sport=sport)
        team_b = Team.objects.create(name='team B', code='BBB', sport=sport)
        tomorrow = datetime.datetime.now(tz=pytz.utc) + datetime.timedelta(days=1)
        for state, name in Tournament._meta.get_field('state').choices:
            tourn = Tournament.objects.create(name='%s_tourn' % name.lower(),
                                              sport=sport,
                                              state=state,
                                              test_features_enabled=True)
            Match.objects.create(tournament=tourn, home_team=team_a, away_team=team_b, kick_off=tomorrow)
            Participant.objects.create(user=test_user1, tournament=tourn)
            Benchmark.objects.create(tournament=tourn, name="all draws",
                                     prediction_algorithm=Benchmark.STATIC,
                                     static_value=0)



    def setUp(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def test_index(self):
        url = reverse('competition:index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_submit_pending(self):
        url = reverse('competition:submit', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit.html')

    def test_submit_active(self):
        url = reverse('competition:submit', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'submit.html')

    def test_submit_finished(self):
        url = reverse('competition:submit', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_submit_archived(self):
        url = reverse('competition:submit', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

    def test_predictions_pending(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_active(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_finished(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_predictions_archived(self):
        url = reverse('competition:predictions', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_table_pending(self):
        url = reverse('competition:table', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_active(self):
        url = reverse('competition:table', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_finished(self):
        url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_table_archived(self):
        url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    @unittest.skip("transaction error")
    def test_join_pending(self):
        url = reverse('competition:join', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='pending_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='pending_tourn'))
        self.assertEqual(count_after, count_before)

        r_url = reverse('competition:submit', kwargs={'tour_name':'pending_tourn'})
        self.assertRedirects(response, r_url)


    @unittest.skip("transaction error")
    def test_join_active(self):
        url = reverse('competition:join', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'join.html')

        count_before = len(Participant.objects.filter(tournament__name='active_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='active_tourn'))
        self.assertEqual(count_after, count_before)

        r_url = reverse('competition:submit', kwargs={'tour_name':'active_tourn'})
        self.assertRedirects(response, r_url)

    def test_join_finished(self):
        url = reverse('competition:join', kwargs={'tour_name':'finished_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)
        count_before = len(Participant.objects.filter(tournament__name='finished_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='finished_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_join_archived(self):
        url = reverse('competition:join', kwargs={'tour_name':'archived_tourn'})
        r_url = reverse('competition:table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, r_url)

        count_before = len(Participant.objects.filter(tournament__name='archived_tourn'))

        response = self.client.post(url)
        count_after = len(Participant.objects.filter(tournament__name='archived_tourn'))
        self.assertEqual(count_after, count_before)

        self.assertRedirects(response, r_url)

    def test_results_pending(self):
        url = reverse('competition:results', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_active(self):
        url = reverse('competition:results', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_finished(self):
        url = reverse('competition:results', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_results_archived(self):
        url = reverse('competition:results', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match_results.html')

    def test_rules_pending(self):
        url = reverse('competition:rules', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_active(self):
        url = reverse('competition:rules', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_finished(self):
        url = reverse('competition:rules', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_rules_archived(self):
        url = reverse('competition:rules', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

    def test_match_pending(self):
        match = Match.objects.filter(tournament__name='pending_tourn')[0]
        url = reverse('competition:match', kwargs={'match_pk': match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match.html')

    def test_match_active(self):
        match = Match.objects.filter(tournament__name='active_tourn')[0]
        url = reverse('competition:match', kwargs={'match_pk': match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match.html')

    def test_match_finished(self):
        match = Match.objects.filter(tournament__name='finished_tourn')[0]
        url = reverse('competition:match', kwargs={'match_pk': match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match.html')

    def test_match_archived(self):
        match = Match.objects.filter(tournament__name='archived_tourn')[0]
        url = reverse('competition:match', kwargs={'match_pk': match.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'match.html')


    def test_benchmark_table_pending(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_active(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_finished(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_table_archived(self):
        url = reverse('competition:benchmark_table', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'table.html')

    def test_benchmark_pending(self):
        benchmark = Benchmark.objects.filter(tournament__name='pending_tourn')[0]
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': benchmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_benchmark_active(self):
        benchmark = Benchmark.objects.filter(tournament__name='active_tourn')[0]
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': benchmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_benchmark_finished(self):
        benchmark = Benchmark.objects.filter(tournament__name='finished_tourn')[0]
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': benchmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')

    def test_benchmark_archived(self):
        benchmark = Benchmark.objects.filter(tournament__name='archived_tourn')[0]
        url = reverse('competition:benchmark', kwargs={'benchmark_pk': benchmark.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'predictions.html')


class HomePageContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('index')
        sport = Sport.objects.create(name='sport')
        tourn_a = Tournament.objects.create(name='tourn_A',
                                            sport=sport,
                                            state=Tournament.ACTIVE)
        tourn_b = Tournament.objects.create(name='tourn_B',
                                            sport=sport,
                                            state=Tournament.ACTIVE)
        tourn_c = Tournament.objects.create(name='tourn_C',
                                  sport=sport,
                                  state=Tournament.ACTIVE)
        Tournament.objects.create(name='tourn_D',
                                  sport=sport,
                                  state=Tournament.FINISHED)

        cls.tourns = [tourn_a, tourn_b, tourn_c]
        cls.user = User.objects.create_user(username='testuser1', password='test123')
        cls.user.save()

        Participant.objects.create(user=cls.user, tournament=tourn_a)
        Participant.objects.create(user=cls.user, tournament=tourn_b)

        cls.team_a = Team.objects.create(name='team A', code='AAA', sport=sport)
        cls.team_b = Team.objects.create(name='team B', code='BBB', sport=sport)

        today = timezone.make_aware(datetime.datetime.combine(datetime.date.today(), datetime.time()))

        cls.times_today = [
            today + datetime.timedelta(hours=6),
            today + datetime.timedelta(hours=12),
            today + datetime.timedelta(hours=18),
        ]
        cls.times_tomorrow = [
            today + datetime.timedelta(days=1, hours=6),
            today + datetime.timedelta(days=1, hours=12),
            today + datetime.timedelta(days=1, hours=18),
        ]


    def setUp(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def test_live_tournaments(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

        self.assertEqual(len(response.context['live_tournaments']), 3)
        self.assertEqual(len(response.context['matches_today']), 0)
        self.assertEqual(len(response.context['matches_tomorrow']), 0)

    def test_todays_matches(self):
        for tourn in self.tourns:
            for time in self.times_today:
                Match.objects.create(tournament=tourn, home_team=self.team_a, away_team=self.team_b, kick_off=time)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

        self.assertEqual(len(response.context['live_tournaments']), 3)
        self.assertEqual(len(response.context['matches_today']), 6)
        self.assertEqual(len(response.context['matches_tomorrow']), 0)

    def test_tomorrows_matches(self):
        for tourn in self.tourns:
            for time in self.times_tomorrow:
                Match.objects.create(tournament=tourn, home_team=self.team_a, away_team=self.team_b, kick_off=time)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

        self.assertEqual(len(response.context['live_tournaments']), 3)
        self.assertEqual(len(response.context['matches_today']), 0)
        self.assertEqual(len(response.context['matches_tomorrow']), 6)

    def test_today_and_tomorrows_matches(self):
        for tourn in self.tourns:
            for time in self.times_today + self.times_tomorrow:
                Match.objects.create(tournament=tourn, home_team=self.team_a, away_team=self.team_b, kick_off=time)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

        self.assertEqual(len(response.context['live_tournaments']), 3)
        self.assertEqual(len(response.context['matches_today']), 6)
        self.assertEqual(len(response.context['matches_tomorrow']), 6)


