from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView, UpdateView

from accounts.decorators import role_required
from booth.forms_sales import InventoryAddForm, InventoryUpdateForm, SaleForm
from booth.mixins import OwnerRequiredMixin, SafeDeleteMixin
from booth.models import Event, EventInventory, Sale, SaleItem


@role_required('OWNER')
def event_inventory(request, event_id):
    event = get_object_or_404(Event, pk=event_id, owner=request.user)
    form = InventoryAddForm(request.POST or None, event=event, owner=request.user)
    if request.method == 'POST' and form.is_valid():
        stock = form.save(commit=False)
        stock.event = event
        stock.current_qty = stock.starting_qty
        stock.save()
        messages.success(request, 'Item added to event stock.')
        return redirect('booth:event_inventory', event_id=event.pk)
    context = {'event': event, 'form': form, 'rows': event.inventory.select_related('item')}
    return render(request, 'booth/event_inventory.html', context)


class InventoryUpdateView(OwnerRequiredMixin, UpdateView):
    form_class = InventoryUpdateForm
    template_name = 'booth/form.html'
    extra_context = {'title': 'Adjust stock'}

    def get_queryset(self):
        return EventInventory.objects.filter(event__owner=self.request.user)

    def get_success_url(self):
        return reverse('booth:event_inventory', args=[self.object.event_id])

    def form_valid(self, form):
        messages.success(self.request, 'Stock updated.')
        return super().form_valid(form)


class InventoryDeleteView(OwnerRequiredMixin, SafeDeleteMixin, DeleteView):
    template_name = 'booth/confirm_delete.html'
    protected_message = 'This stock row is used in sales and cannot be removed.'
    success_message = 'Removed from event stock.'

    def get_queryset(self):
        return EventInventory.objects.filter(event__owner=self.request.user)

    def get_success_url(self):
        return reverse('booth:event_inventory', args=[self.object.event_id])


def _can_record(user, event):
    return event.owner_id == user.id or event.assistants.filter(pk=user.pk).exists()


@login_required
def record_sale(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if not _can_record(request.user, event):
        messages.error(request, 'You are not assigned to that event.')
        return redirect('dashboard')
    if event.status != Event.Status.ONGOING:
        messages.error(request, 'Sales can only be recorded while the event is Ongoing.')
        return redirect('dashboard')

    form = SaleForm(request.POST or None, event=event)
    if request.method == 'POST' and form.is_valid():
        items = form.cleaned_data['items']
        with transaction.atomic():
            locked = EventInventory.objects.select_for_update().in_bulk([row.pk for row, _ in items])
            short = [row.item.name for row, qty in items if locked[row.pk].current_qty < qty]
            if short:
                form.add_error(None, 'Not enough stock for: ' + ', '.join(short) + '.')
            else:
                sale = Sale.objects.create(
                    event=event, recorded_by=request.user,
                    payment_method=form.cleaned_data['payment_method'],
                )
                total = Decimal('0')
                for row, qty in items:
                    stock = locked[row.pk]
                    price = stock.item.unit_price
                    SaleItem.objects.create(sale=sale, inventory=stock, quantity=qty, unit_price=price)
                    stock.current_qty -= qty
                    stock.save(update_fields=['current_qty'])
                    total += price * qty
                sale.total_amount = total
                sale.save(update_fields=['total_amount'])
                messages.success(request, f'Sale recorded. Total: ₱{total}')
                return redirect('booth:sale_list')
    return render(request, 'booth/sale_form.html', {'event': event, 'form': form})


@login_required
def sale_list(request):
    if request.user.role == 'OWNER':
        sales = Sale.objects.filter(event__owner=request.user)
    else:
        sales = Sale.objects.filter(recorded_by=request.user)
    sales = sales.select_related('event', 'recorded_by').prefetch_related('items__inventory__item')
    return render(request, 'booth/sale_list.html', {'sales': sales})


@require_POST
@role_required('OWNER')
def void_sale(request, pk):
    with transaction.atomic():
        sale = get_object_or_404(
            Sale.objects.select_for_update(of=('self',)), pk=pk, event__owner=request.user
        )
        if sale.status != Sale.Status.COMPLETED:
            messages.error(request, 'This sale is already voided.')
        else:
            for line in sale.items.all():
                EventInventory.objects.filter(pk=line.inventory_id).update(
                    current_qty=F('current_qty') + line.quantity
                )
            sale.status = Sale.Status.VOIDED
            sale.save(update_fields=['status'])
            messages.success(request, f'Sale #{sale.pk} voided and stock restored.')
    return redirect('booth:sale_list')