from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.core.urlresolvers import reverse
import unittest
import re
# import pdb; pdb.set_trace()

class ServerViewTest (TestCase):

    @classmethod
    def setUpTestData(cls):
        #print("setuptestdata: run once to set up non-modified data for all class methods.")
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()

    def test_index(self):
        url = reverse('index')
        r_url = reverse('login')
        response = self.client.get(url)
        self.assertRedirects(response, r_url + '?next=' + url)

        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'home.html')
        self.assertEqual(len(response.context['live_tournaments']), 0)

    def test_signup_logged_out(self):
        url = reverse('signup')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_activate_logged_out(self):
        response = self.client.get('/activate/NTg3/5is-557c19a28c27875f3213/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/activation_invalid.html')

    def test_about_logged_out(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    def test_gdpr_logged_out(self):
        response = self.client.get('/gdpr/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'gdpr.html')

    def test_login_logout(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/accounts/logout/')
        self.assertRedirects(response, '/', target_status_code=302)

        response = self.client.get('/')
        self.assertRedirects(response, '/accounts/login/?next=/')


class SignupTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        test_user1 = User.objects.create_user(username='testuser1',
                                              password='test123',
                                              email='test@example.com')
        test_user1.save()

        cls.url_signup = reverse('signup')
        cls.url_index = reverse('index')
        cls.url_login = reverse('login')

    def test_signup(self):
        response = self.client.post(self.url_signup, {
            'username': 'new_user',
            'password1': 'password',
            'password2': 'password',
            'email': 'new_user@example.com',
            'cookie_consent': 1,
            'display_name_format': 1,
            'g-recaptcha-response': 'PASSED',
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

        response = self.client.get(self.url_index)
        self.assertRedirects(response, self.url_login + '?next=' + self.url_index)

        m = re.search('https?://example.com(/.*/)', email.body)
        self.assertIsNotNone(m)

        response = self.client.get(m.group(1))
        self.assertRedirects(response, self.url_index)

        user = User.objects.get(username='new_user')
        self.assertTrue(user.is_active)

        login = self.client.login(username='new_user', password='password')
        self.assertTrue(login)

        response = self.client.get(self.url_index)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_signup_duplicate_username(self):

        users = User.objects.filter(username='testuser1')
        self.assertEqual(len(users), 1)

        response = self.client.post(self.url_signup, {
            'username': 'testuser1',
            'password1': 'password',
            'password2': 'password',
            'email': 'new_user@example.com',
            'cookie_consent': 1,
            'display_name_format': 1,
            'g-recaptcha-response': 'PASSED',
            })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

        self.assertEqual(len(mail.outbox), 0)

        users = User.objects.filter(username='testuser1')
        self.assertEqual(len(users), 1)

        self.assertEqual(users[0].email, 'test@example.com')

        login = self.client.login(username='testuser1', password='password')
        self.assertFalse(login)

    def test_signup_duplicate_email(self):
        user = User.objects.get(username='testuser1')
        self.assertEqual(user.email, 'test@example.com')

        response = self.client.post(self.url_signup, {
            'username': 'new_user',
            'password1': 'password',
            'password2': 'password',
            'email': 'test@example.com',
            'cookie_consent': 1,
            'display_name_format': 1,
            'g-recaptcha-response': 'PASSED',
            })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

        self.assertEqual(len(mail.outbox), 0)

        users = User.objects.filter(username='new_user')
        self.assertEqual(len(users), 0)

        login = self.client.login(username='new_user', password='password')
        self.assertFalse(login)

    def test_signup_password_missmatch(self):
        response = self.client.post(self.url_signup, {
            'username': 'new_user',
            'password1': 'password1',
            'password2': 'password2',
            'email': 'new_user@example.com',
            'cookie_consent': 1,
            'display_name_format': 1,
            'g-recaptcha-response': 'PASSED',
            })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

        self.assertEqual(len(mail.outbox), 0)

        users = User.objects.filter(username='new_user')
        self.assertEqual(len(users), 0)

        login = self.client.login(username='new_user', password='password1')
        self.assertFalse(login)

