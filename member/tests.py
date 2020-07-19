from django.contrib.auth.models import User, Permission
from django.core.urlresolvers import reverse
from django.test import TestCase

import unittest

from .models import Organisation, Competition, Ticket
from competition.models import Tournament, Sport


class MemberViewLoggedOutTest(TestCase):
    def test_profile(self):
        url = reverse('member:profile')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_use_token(self):
        url = reverse('member:use_token')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_announcement(self):
        url = reverse('member:announcement')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

    def test_tickets(self):
        url = reverse('member:tickets', kwargs={'comp_pk': 1})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)


class MemberViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        test_user1 = User.objects.create_user(username='testuser1', password='test123')
        test_user1.save()

        sport = Sport.objects.create(name='sport')
        tourn = Tournament.objects.create(name='active_tourn', sport=sport, state=Tournament.ACTIVE)
        org = Organisation.objects.create(name="Test")
        comp = Competition.objects.create(organisation=org, tournament=tourn)
        Ticket.objects.create(competition=comp)

    def setUp(self):
        login = self.client.login(username='testuser1', password='test123')
        self.assertTrue(login)

    def test_profile(self):
        url = reverse('member:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_use_token(self):
        url = reverse('member:use_token')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'token.html')

    def test_announcement(self):
        url = reverse('member:announcement')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        user = User.objects.get(username='testuser1')
        user.is_superuser = True
        user.save()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcement.html')

    @unittest.skip("missing logo for org")
    def test_tickets(self):
        comp = Competition.objects.get(organisation__name="Test")
        url = reverse('member:tickets', kwargs={'comp_pk': comp.pk})
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login') + "?next=" + url)

        permission = Permission.objects.get(name='Can change match')
        user = User.objects.get(username='testuser1')
        user.user_permissions.add(permission)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets.html')

