from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
import unittest

class ServerViewTest (TestCase):

    @classmethod
    def setUpTestData(cls):
        #print("setUpTestData: Run once to set up non-modified data for all class methods.")
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()

    def test_index_logged_out(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_index_logged_in(self):
        login = self.client.login(username='testuser1', password='test123')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_signup_logged_out(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    @unittest.skip("TODO")
    def test_activate_logged_out(self):
        response = self.client.get('/activate/')
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_about_logged_out(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_gdpr_logged_out(self):
        response = self.client.get('/gdpr/')
        self.assertEqual(response.status_code, 200)


class SignupTest(TestCase):
    def test_signup(self):
        response = self.client.post('/register/', {
            'username': 'new_user',
            'password1': 'password',
            'password2': 'password',
            'email': 'new_user@example.com',
            'cookie_consent': 0,
            'display_name_format': 0,
            })

        self.assertRedirects(response, '/register/activation_sent/')

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        self.assertEqual(mail.outbox[0].subject, 'Activate Your Account')
        self.assertEqual(mail.outbox[0].to, ['new_user@example.com'])

