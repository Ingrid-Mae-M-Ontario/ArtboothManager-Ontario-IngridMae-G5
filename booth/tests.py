from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from booth.models import Event, EventStock, Item, Sale, SaleLine
from booth.services import record_sale


class BoothFeatureTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='test-password',
            role=User.Role.OWNER,
        )
        self.other_owner = User.objects.create_user(
            username='other-owner', email='other@example.com', password='test-password',
            role=User.Role.OWNER,
        )
        self.assistant = User.objects.create_user(
            username='assistant', email='assistant@example.com', password='test-password',
            role=User.Role.ASSISTANT,
        )
        self.item = Item.objects.create(owner=self.owner, name='Print', unit_price=Decimal('12.50'))
        self.other_item = Item.objects.create(
            owner=self.other_owner, name='Other Print', unit_price=Decimal('15.00')
        )
        self.event = Event.objects.create(
            owner=self.owner, name='Art Fair', venue='Community Hall',
            start_date=date(2026, 12, 1), end_date=date(2026, 12, 2),
        )
        self.event.assistants.add(self.assistant)
        self.other_event = Event.objects.create(
            owner=self.other_owner, name='Private Fair', venue='Other Hall',
            start_date=date(2026, 12, 3), end_date=date(2026, 12, 4),
        )

    def test_owner_item_list_only_shows_own_items(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('booth:item_list'))

        self.assertContains(response, self.item.name)
        self.assertNotContains(response, self.other_item.name)

    def test_owner_can_create_update_and_delete_item(self):
        self.client.force_login(self.owner)
        item_list_url = reverse('booth:item_list')

        response = self.client.post(reverse('booth:item_create'), {
            'name': 'Sticker', 'unit_price': '2.50', 'is_active': 'on',
        })
        created_item = Item.objects.get(name='Sticker', owner=self.owner)
        self.assertRedirects(response, item_list_url)

        response = self.client.post(reverse('booth:item_update', args=[created_item.pk]), {
            'name': 'Large Sticker', 'unit_price': '3.50', 'is_active': 'on',
        })
        created_item.refresh_from_db()
        self.assertEqual(created_item.name, 'Large Sticker')
        self.assertRedirects(response, item_list_url)

        response = self.client.post(reverse('booth:item_delete', args=[created_item.pk]))
        self.assertRedirects(response, item_list_url)
        self.assertFalse(Item.objects.filter(pk=created_item.pk).exists())

    def test_item_form_rejects_duplicate_name_and_nonpositive_price(self):
        self.client.force_login(self.owner)

        duplicate_response = self.client.post(reverse('booth:item_create'), {
            'name': 'print', 'unit_price': '12.50', 'is_active': 'on',
        })
        self.assertContains(duplicate_response, 'already have an item with this name')

        invalid_price_response = self.client.post(reverse('booth:item_create'), {
            'name': 'Invalid Price Item', 'unit_price': '0.00', 'is_active': 'on',
        })
        self.assertContains(invalid_price_response, 'Ensure this value is greater than or equal to 0.01')

    def test_owner_cannot_access_another_owners_item(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('booth:item_update', args=[self.other_item.pk]))

        self.assertEqual(response.status_code, 404)

    def test_event_form_rejects_end_date_before_start_date(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('booth:event_create'), {
            'name': 'Invalid Dates', 'venue': 'Community Hall',
            'start_date': '2026-12-10', 'end_date': '2026-12-09',
            'status': Event.Status.PLANNED,
        })

        self.assertContains(response, 'End date cannot be earlier than the start date')
        self.assertFalse(Event.objects.filter(name='Invalid Dates').exists())

    def test_owner_can_create_update_and_delete_event(self):
        self.client.force_login(self.owner)
        event_list_url = reverse('booth:event_list')

        response = self.client.post(reverse('booth:event_create'), {
            'name': 'Winter Market', 'venue': 'Convention Center',
            'start_date': '2026-12-10', 'end_date': '2026-12-11',
            'status': Event.Status.PLANNED, 'assistants': [self.assistant.pk],
        })
        created_event = Event.objects.get(name='Winter Market', owner=self.owner)
        self.assertIn(self.assistant, created_event.assistants.all())
        self.assertRedirects(response, event_list_url)

        response = self.client.post(reverse('booth:event_update', args=[created_event.pk]), {
            'name': 'Winter Art Market', 'venue': 'Convention Center',
            'start_date': '2026-12-10', 'end_date': '2026-12-12',
            'status': Event.Status.ONGOING, 'assistants': [self.assistant.pk],
        })
        created_event.refresh_from_db()
        self.assertEqual(created_event.name, 'Winter Art Market')
        self.assertEqual(created_event.status, Event.Status.ONGOING)
        self.assertRedirects(response, event_list_url)

        response = self.client.post(reverse('booth:event_delete', args=[created_event.pk]))
        self.assertRedirects(response, event_list_url)
        self.assertFalse(Event.objects.filter(pk=created_event.pk).exists())

    def test_owner_cannot_access_another_owners_event(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('booth:event_update', args=[self.other_event.pk]))

        self.assertEqual(response.status_code, 404)

    def test_assistant_sees_only_assigned_events_read_only(self):
        self.client.force_login(self.assistant)

        response = self.client.get(reverse('booth:assistant_event_list'))

        self.assertContains(response, self.event.name)
        self.assertNotContains(response, self.other_event.name)
        self.assertNotContains(response, reverse('booth:event_update', args=[self.event.pk]))

    def test_assistant_cannot_use_owner_management_pages(self):
        self.client.force_login(self.assistant)

        response = self.client.get(reverse('booth:event_list'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard'))

    def test_owner_can_add_and_adjust_event_stock(self):
        self.client.force_login(self.owner)
        stock_url = reverse('booth:stock_list', args=[self.event.pk])

        response = self.client.post(reverse('booth:stock_create', args=[self.event.pk]), {
            'item': self.item.pk, 'quantity': 8,
        })
        stock = EventStock.objects.get(event=self.event, item=self.item)
        self.assertEqual(stock.quantity, 8)
        self.assertRedirects(response, stock_url)

        response = self.client.post(
            reverse('booth:stock_update', args=[self.event.pk, stock.pk]),
            {'item': self.item.pk, 'quantity': 11},
        )
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, 11)
        self.assertRedirects(response, stock_url)

    def test_owner_cannot_change_stock_item_after_sales_exist(self):
        stock = EventStock.objects.create(event=self.event, item=self.item, quantity=5)
        record_sale(
            event_id=self.event.pk, stock_id=stock.pk, quantity=1, actor=self.assistant,
        )
        self.client.force_login(self.owner)

        self.client.post(
            reverse('booth:stock_update', args=[self.event.pk, stock.pk]),
            {'item': self.other_item.pk, 'quantity': 4},
        )

        stock.refresh_from_db()
        self.assertEqual(stock.item_id, self.item.pk)
        self.assertEqual(stock.quantity, 4)

    def test_owner_cannot_use_stock_from_another_owners_event(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('booth:stock_list', args=[self.other_event.pk]))

        self.assertEqual(response.status_code, 404)

    def test_sale_deducts_event_stock_and_keeps_price_snapshot(self):
        stock = EventStock.objects.create(event=self.event, item=self.item, quantity=5)
        self.client.force_login(self.assistant)

        response = self.client.post(reverse('booth:sale_create', args=[self.event.pk]), {
            'stock': stock.pk, 'quantity': 2,
        })

        stock.refresh_from_db()
        sale = Sale.objects.get(event=self.event, recorded_by=self.assistant)
        line = SaleLine.objects.get(sale=sale)
        self.assertEqual(stock.quantity, 3)
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.unit_price, self.item.unit_price)
        self.assertEqual(sale.total, Decimal('25.00'))
        self.assertRedirects(response, reverse('booth:sales_list', args=[self.event.pk]))

    def test_sale_history_keeps_original_item_name_and_price(self):
        stock = EventStock.objects.create(event=self.event, item=self.item, quantity=2)
        sale = record_sale(
            event_id=self.event.pk, stock_id=stock.pk, quantity=1, actor=self.assistant,
        )
        self.item.name = 'Renamed Print'
        self.item.unit_price = Decimal('20.00')
        self.item.save()
        self.client.force_login(self.owner)

        response = self.client.get(reverse('booth:sales_list', args=[self.event.pk]))

        self.assertContains(response, 'Print')
        self.assertNotContains(response, 'Renamed Print')
        self.assertEqual(sale.total, Decimal('12.50'))

    def test_overselling_is_rejected_without_creating_a_sale(self):
        stock = EventStock.objects.create(event=self.event, item=self.item, quantity=1)
        self.client.force_login(self.assistant)

        response = self.client.post(reverse('booth:sale_create', args=[self.event.pk]), {
            'stock': stock.pk, 'quantity': 2,
        })

        stock.refresh_from_db()
        self.assertContains(response, 'Quantity exceeds the available event stock')
        self.assertEqual(stock.quantity, 1)
        self.assertFalse(Sale.objects.filter(event=self.event).exists())

    def test_voiding_sale_restores_stock_only_once(self):
        stock = EventStock.objects.create(event=self.event, item=self.item, quantity=5)
        self.client.force_login(self.assistant)
        sale = record_sale(
            event_id=self.event.pk, stock_id=stock.pk, quantity=3, actor=self.assistant,
        )
        self.client.force_login(self.owner)
        void_url = reverse('booth:sale_void', args=[self.event.pk, sale.pk])

        first_response = self.client.post(void_url)
        stock.refresh_from_db()
        sale.refresh_from_db()
        self.assertEqual(stock.quantity, 5)
        self.assertEqual(sale.status, Sale.Status.VOID)
        self.assertEqual(sale.voided_by, self.owner)
        self.assertRedirects(first_response, reverse('booth:sales_list', args=[self.event.pk]))

        self.client.post(void_url)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, 5)

    def test_stock_cannot_be_removed_after_sales_are_recorded(self):
        stock = EventStock.objects.create(event=self.event, item=self.item, quantity=2)
        record_sale(
            event_id=self.event.pk, stock_id=stock.pk, quantity=1, actor=self.assistant,
        )
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('booth:stock_delete', args=[self.event.pk, stock.pk]),
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(EventStock.objects.filter(pk=stock.pk).exists())

    def test_assistant_cannot_void_another_assistants_sale(self):
        other_assistant = User.objects.create_user(
            username='assistant-two', email='assistant-two@example.com', password='test-password',
            role=User.Role.ASSISTANT,
        )
        self.event.assistants.add(other_assistant)
        stock = EventStock.objects.create(event=self.event, item=self.item, quantity=5)
        sale = record_sale(
            event_id=self.event.pk, stock_id=stock.pk, quantity=1, actor=self.assistant,
        )
        self.client.force_login(other_assistant)

        self.client.post(reverse('booth:sale_void', args=[self.event.pk, sale.pk]))

        stock.refresh_from_db()
        sale.refresh_from_db()
        self.assertEqual(stock.quantity, 4)
        self.assertEqual(sale.status, Sale.Status.COMPLETED)

    def test_assistant_cannot_manage_event_stock(self):
        self.client.force_login(self.assistant)

        response = self.client.get(reverse('booth:stock_list', args=[self.event.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('dashboard'))

    def test_closed_event_rejects_sales(self):
        self.event.status = Event.Status.CLOSED
        self.event.save()
        stock = EventStock.objects.create(event=self.event, item=self.item, quantity=2)
        self.client.force_login(self.assistant)

        response = self.client.post(reverse('booth:sale_create', args=[self.event.pk]), {
            'stock': stock.pk, 'quantity': 1,
        })

        stock.refresh_from_db()
        self.assertContains(response, 'Sales cannot be recorded for a closed event')
        self.assertEqual(stock.quantity, 2)
        self.assertFalse(Sale.objects.filter(event=self.event).exists())

    def test_feature_pages_require_login(self):
        response = self.client.get(reverse('booth:item_list'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('booth:item_list')}",
        )
