from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class StandardFeatureTests(TestCase):
    def test_registration_creates_account(self):
        response = self.client.post(reverse('register'), {
            'username': 'newowner',
            'email': 'newowner@example.com',
            'first_name': 'New',
            'last_name': 'Owner',
            'role': User.Role.OWNER,
            'contact_number': '09123456789',
            'password1': 'StrongPass!123',
            'password2': 'StrongPass!123',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(User.objects.filter(username='newowner').exists())

    def test_profile_blocks_another_user_id(self):
        user = User.objects.create_user(
            username='profile', email='profile@example.com', password='StrongPass!123',
            role=User.Role.OWNER,
        )
        self.client.force_login(user)
        response = self.client.get(reverse('profile') + '?pk=999')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], user)
