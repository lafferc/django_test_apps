from django.contrib.auth.models import User
from django.test import TestCase
from django.core.urlresolvers import reverse

from .models import Sport, Tournament, Participant

class CompetitionViewLoggedOutTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def test_redirect_if_not_logged_in(self):
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

    def test_logged_in_uses_correct_template(self):
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

    def test_user_active_submit(self):
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

    def test_user_finished_join(self):
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

    def test_results_active(self):
        url = reverse('competition:results', kwargs={'tour_name':'active_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_results_finished(self):
        url = reverse('competition:results', kwargs={'tour_name':'finished_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_results_archived(self):
        url = reverse('competition:results', kwargs={'tour_name':'archived_tourn'})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_rules_pending(self):
        url = reverse('competition:rules', kwargs={'tour_name':'pending_tourn'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_rules.html')

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
#     def test_benchmark_table_pending(self):
#     def test_benchmark_table_active(self):
#     def test_benchmark_table_finished(self):
#     def test_benchmark_table_archived(self):
# 
#     def test_benchmark_pending(self):
#     def test_benchmark_active(self):
#     def test_benchmark_finished(self):
#     def test_benchmark_archived(self):
