from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from booth.models import Event, EventInventory, Item, Sale


class CoreFeatureHardeningTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='StrongPass!123',
            role=User.Role.OWNER,
        )
        self.assistant = User.objects.create_user(
            username='assistant', email='assistant@example.com', password='StrongPass!123',
            role=User.Role.ASSISTANT,
        )
        self.other_owner = User.objects.create_user(
            username='other', email='other@example.com', password='StrongPass!123',
            role=User.Role.OWNER,
        )
        self.item = Item.objects.create(owner=self.owner, name='Sticker', unit_price=Decimal('50.00'))
        start = timezone.localdate()
        self.event = Event.objects.create(
            owner=self.owner, name='Comic Con', venue='Hall A',
            start_date=start, end_date=start + timedelta(days=1),
            status=Event.Status.ONGOING,
        )
        self.event.assistants.add(self.assistant)
        self.inventory = EventInventory.objects.create(
            event=self.event, item=self.item, starting_qty=10, current_qty=10,
        )

    def test_valid_item_creation(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('booth:item_create'), {
            'name': 'Print',
            'unit_price': '120.00',
            'is_active': 'on',
        })
        self.assertRedirects(response, reverse('booth:item_list'))
        self.assertTrue(Item.objects.filter(owner=self.owner, name='Print').exists())

    def test_invalid_duplicate_item_name(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('booth:item_create'), {
            'name': ' sticker ',
            'unit_price': '50.00',
            'is_active': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'already have an item')

    def test_invalid_event_dates_are_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('booth:event_create'), {
            'name': 'Bad Event',
            'venue': 'Hall B',
            'start_date': timezone.localdate(),
            'end_date': timezone.localdate() - timedelta(days=1),
            'status': Event.Status.PLANNED,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'End date cannot be earlier')

    def test_login_is_required_for_core_view(self):
        response = self.client.get(reverse('booth:sale_list'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('booth:sale_list')}")

    def test_owner_cannot_view_other_owner_item(self):
        other_item = Item.objects.create(owner=self.other_owner, name='Secret', unit_price=Decimal('10.00'))
        self.client.force_login(self.owner)
        response = self.client.get(reverse('booth:item_update', args=[other_item.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_cannot_void_another_owner_sale(self):
        sale = Sale.objects.create(
            event=Event.objects.create(
                owner=self.other_owner, name='Other Event', venue='Hall C',
                start_date=timezone.localdate(), end_date=timezone.localdate(),
                status=Event.Status.ONGOING,
            ),
            recorded_by=self.other_owner,
            payment_method=Sale.PaymentMethod.CASH,
        )
        self.client.force_login(self.owner)
        response = self.client.post(reverse('booth:void_sale', args=[sale.pk]))
        self.assertEqual(response.status_code, 404)
        sale.refresh_from_db()
        self.assertEqual(sale.status, Sale.Status.COMPLETED)

    def test_valid_sale_deducts_stock(self):
        self.client.force_login(self.assistant)
        response = self.client.post(reverse('booth:record_sale', args=[self.event.pk]), {
            'payment_method': Sale.PaymentMethod.CASH,
            f'qty_{self.inventory.pk}': '3',
        })
        self.assertRedirects(response, reverse('booth:sale_list'))
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.current_qty, 7)
        sale = Sale.objects.get(event=self.event)
        self.assertEqual(sale.total_amount, Decimal('150.00'))

    def test_invalid_sale_quantity_does_not_change_stock(self):
        self.client.force_login(self.assistant)
        response = self.client.post(reverse('booth:record_sale', args=[self.event.pk]), {
            'payment_method': Sale.PaymentMethod.CASH,
            f'qty_{self.inventory.pk}': '11',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Only 10 in stock')
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.current_qty, 10)

    def test_unassigned_assistant_is_blocked_from_sale(self):
        self.event.assistants.clear()
        self.client.force_login(self.assistant)
        response = self.client.post(reverse('booth:record_sale', args=[self.event.pk]), {
            'payment_method': Sale.PaymentMethod.CASH,
            f'qty_{self.inventory.pk}': '1',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.current_qty, 10)

    def test_void_sale_restores_stock(self):
        self.client.force_login(self.assistant)
        self.client.post(reverse('booth:record_sale', args=[self.event.pk]), {
            'payment_method': Sale.PaymentMethod.CASH,
            f'qty_{self.inventory.pk}': '4',
        })
        sale = Sale.objects.get(event=self.event)
        self.client.force_login(self.owner)
        response = self.client.post(reverse('booth:void_sale', args=[sale.pk]))
        self.assertRedirects(response, reverse('booth:sale_list'))
        sale.refresh_from_db()
        self.inventory.refresh_from_db()
        self.assertEqual(sale.status, Sale.Status.VOIDED)
        self.assertEqual(self.inventory.current_qty, 10)

    def test_void_sale_rejects_get_request(self):
        sale = Sale.objects.create(
            event=self.event, recorded_by=self.assistant,
            payment_method=Sale.PaymentMethod.CASH,
        )
        self.client.force_login(self.owner)
        response = self.client.get(reverse('booth:void_sale', args=[sale.pk]))
        self.assertEqual(response.status_code, 405)

    def test_invalid_url_returns_not_found_page(self):
        self.client.force_login(self.owner)
        response = self.client.get('/booth/items/999999/edit/')
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, '404', status_code=404)
