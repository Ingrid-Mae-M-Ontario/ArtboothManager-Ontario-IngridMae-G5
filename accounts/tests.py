from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class AccountFeatureTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='test-password',
            role=User.Role.OWNER,
        )

    def test_registration_creates_account(self):
        response = self.client.post(reverse('register'), {
            'username': 'new-owner',
            'email': 'new-owner@example.com',
            'first_name': 'New',
            'last_name': 'Owner',
            'role': User.Role.OWNER,
            'contact_number': '',
            'password1': 'Safe-test-pass-348!',
            'password2': 'Safe-test-pass-348!',
        })

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='new-owner').exists())

    def test_login_redirects_owner_to_owner_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': self.owner.username,
            'password': 'test-password',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.redirect_chain,
            [(reverse('dashboard'), 302), (reverse('owner_dashboard'), 302)],
        )

    def test_logout_ends_session(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_profile_updates_only_logged_in_users_profile(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('profile'), {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'owner@example.com',
            'contact_number': '555-0123',
        })
        self.owner.refresh_from_db()

        self.assertRedirects(response, reverse('profile'))
        self.assertEqual(self.owner.first_name, 'Updated')
        self.assertEqual(self.owner.contact_number, '555-0123')

    def test_role_dashboard_is_restricted(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('assistant_dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard'))

# Create your tests here.
