from django.contrib.auth.models import User
from django.test import TestCase

from .models import Sport, Tournament, Participant

# Create your tests here.
class RedirectUsersToCorrectViewTest (TestCase):
    @classmethod
    def setUpTestData(cls):
        #print("setUpTestData: Run once to set up non-modified data for all class methods.")
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()
        test_user2 = User.objects.create_user(username='testuser2', password='test123')
        test_user2.save()

        sport = Sport.objects.create(name='football')
        for state, name in Tournament._meta.get_field('state').choices:
            Tournament.objects.create(name='%s_tourn' % name, sport=sport)

    def setUp(self):
        #print("setUp: Run once for every test method to setup clean data.")
        pass

    def tearDown(self):
        #print("tearDown: Run after every test method")
        pass

    def test_redirect_if_not_logged_in(self):
        response = self.client.get('/competition/')
        self.assertRedirects(response, '/accounts/login/?next=/competition/')

    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username='testuser1', password='test123')
        response = self.client.get('/competition/')
        
        # Check our user is logged in
        self.assertEqual(str(response.context['user']), 'testuser1')
        # Check that we got a response "success"
        self.assertEqual(response.status_code, 200)

        # Check we used correct template
        self.assertTemplateUsed(response, 'index.html')

    def test_user_active_submit(self):
        login = self.client.login(username='testuser1', password='test123')
        response = self.client.get('/competition/Active_tourn/')
        self.assertRedirects(response, '/competition/Active_tourn/join/')

    def test_user_finished_join(self):
        login = self.client.login(username='testuser1', password='test123')
        response = self.client.get('/competition/Active_tourn/')
        self.assertRedirects(response, '/competition/Active_tourn/table/')

