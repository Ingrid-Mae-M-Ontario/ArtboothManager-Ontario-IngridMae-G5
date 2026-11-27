from django import forms
from django.core.exceptions import ValidationError

from booth.forms import style
from booth.models import EventInventory, Item, Sale


class InventoryAddForm(forms.ModelForm):
    class Meta:
        model = EventInventory
        fields = ('item', 'starting_qty')

    def __init__(self, *args, event=None, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        self.fields['item'].queryset = (
            Item.objects.filter(owner=owner, is_active=True).exclude(event_stock__event=event)
        )
        style(self)

    def clean_starting_qty(self):
        quantity = self.cleaned_data['starting_qty']
        if quantity < 1:
            raise ValidationError('Starting stock must be at least 1.')
        return quantity


class InventoryUpdateForm(forms.ModelForm):
    class Meta:
        model = EventInventory
        fields = ('starting_qty', 'current_qty')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self)

    def clean(self):
        data = super().clean()
        starting = data.get('starting_qty')
        current = data.get('current_qty')
        if starting is not None and current is not None:
            if starting < 1:
                self.add_error('starting_qty', 'Starting stock must be at least 1.')
            if current < 0:
                self.add_error('current_qty', 'Current stock cannot be negative.')
            if starting is not None and current is not None and current > starting:
                self.add_error('current_qty', 'Current stock cannot exceed starting stock.')
        return data


class SaleForm(forms.Form):
    payment_method = forms.ChoiceField(choices=Sale.PaymentMethod.choices)

    def __init__(self, *args, event, **kwargs):
        super().__init__(*args, **kwargs)
        self.rows = list(event.inventory.select_related('item').filter(item__is_active=True))
        for row in self.rows:
            self.fields[f'qty_{row.pk}'] = forms.IntegerField(
                min_value=0, required=False, initial=0,
                label=f'{row.item.name} (₱{row.item.unit_price}, {row.current_qty} in stock)',
            )
        style(self)

    def clean(self):
        data = super().clean()
        items = []
        for row in self.rows:
            qty = data.get(f'qty_{row.pk}') or 0
            if qty > row.current_qty:
                self.add_error(f'qty_{row.pk}', f'Only {row.current_qty} in stock.')
            elif qty > 0:
                items.append((row, qty))
        if not items and not self.errors:
            raise ValidationError('Enter a quantity for at least one item.')
        data['items'] = items
        return data