from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
import unittest
import re
#import pdb; pdb.set_trace()

class ServerViewTest (TestCase):

    @classmethod
    def setUpTestData(cls):
        #print("setuptestdata: run once to set up non-modified data for all class methods.")
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()

    def test_index_logged_out(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_index_logged_in(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_signup_logged_out(self):
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)

    def test_activate_logged_out(self):
        response = self.client.get('/activate/')
        self.assertEqual(response.status_code, 404)

    def test_about_logged_out(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)

    def test_gdpr_logged_out(self):
        response = self.client.get('/gdpr/')
        self.assertEqual(response.status_code, 200)


class SignupTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user1 = User.objects.create_user(username='testuser1',
                                              password='test123',
                                              email='test@example.com')
        test_user1.save()

    def test_signup(self):
        response = self.client.post('/register/', {
            'username': 'new_user',
            'password1': 'password',
            'password2': 'password',
            'email': 'new_user@example.com',
            'cookie_consent': 1,
            'display_name_format': 1,
            })

        self.assertRedirects(response, '/register/activation_sent/')

        user = User.objects.get(username='new_user')

        self.assertEqual(user.email, 'new_user@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(user.profile.cookie_consent, 1)
        self.assertEqual(user.profile.display_name_format, 1)

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(email.subject, 'Activate Your Account')
        self.assertEqual(email.to, ['new_user@example.com'])

        login = self.client.login(username='new_user', password='password')
        self.assertFalse(login)

        m = re.search('https?://testserver(/.*/)', email.body)
        self.assertIsNotNone(m)

        response = self.client.get(m.group(1))
        self.assertRedirects(response, '/')

        user = User.objects.get(username='new_user')
        self.assertTrue(user.is_active)

        login = self.client.login(username='new_user', password='password')
        self.assertTrue(login)

    @unittest.skip("500 server error")
    def test_signup_duplicate_username(self):

        user = User.objects.get(username='testuser1')

        response = self.client.post('/register/', {
            'username': 'testuser1',
            'password1': 'password',
            'password2': 'password',
            'email': 'new_user@example.com',
            'cookie_consent': 1,
            'display_name_format': 1,
            })

        self.assertEqual(len(mail.outbox), 0)

        login = self.client.login(username='testuser1', password='password')
        self.assertFalse(login)

    def test_signup_duplicate_email(self):
        user = User.objects.get(username='testuser1')
        self.assertEqual(user.email, 'test@example.com')

        response = self.client.post('/register/', {
            'username': 'new_user',
            'password1': 'password',
            'password2': 'password',
            'email': 'test@example.com',
            'cookie_consent': 1,
            'display_name_format': 1,
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'registration/register.html')

        self.assertEqual(len(mail.outbox), 0)

        try:
            user = User.objects.get(username='new_user')
        except User.DoesNotExist:
            user = None

        self.assertIsNone(user)

        login = self.client.login(username='new_user', password='password')
        self.assertFalse(login)

    def test_signup_password_missmatch(self):
        response = self.client.post('/register/', {
            'username': 'new_user',
            'password1': 'password1',
            'password2': 'password2',
            'email': 'new_user@example.com',
            'cookie_consent': 1,
            'display_name_format': 1,
            })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'registration/register.html')

        self.assertEqual(len(mail.outbox), 0)

        try:
            user = User.objects.get(username='new_user')
        except User.DoesNotExist:
            user = None

        self.assertIsNone(user)

        login = self.client.login(username='new_user', password='password1')
        self.assertFalse(login)

