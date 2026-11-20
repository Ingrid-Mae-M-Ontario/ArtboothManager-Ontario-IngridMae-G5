from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User
from booth.models import Event, EventStock, Item


def style(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, forms.CheckboxSelectMultiple):
            continue
        if isinstance(widget, forms.CheckboxInput):
            widget.attrs['class'] = 'form-check-input'
        elif isinstance(widget, forms.Select):
            widget.attrs['class'] = 'form-select'
        else:
            widget.attrs['class'] = 'form-control'


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ('name', 'unit_price', 'is_active')

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        style(self)

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        duplicates = Item.objects.filter(owner=self.owner, name__iexact=name).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise ValidationError('You already have an item with this name.')
        return name


class EventForm(forms.ModelForm):
    assistants = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='ASSISTANT'),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Event
        fields = ('name', 'venue', 'start_date', 'end_date', 'status', 'assistants')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'end_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style(self)


class EventStockForm(forms.ModelForm):
    class Meta:
        model = EventStock
        fields = ('item', 'quantity')

    def __init__(self, *args, event, owner, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        self.fields['item'].queryset = Item.objects.filter(owner=owner)
        if self.instance.pk is None:
            self.fields['item'].queryset = self.fields['item'].queryset.filter(is_active=True)
        elif self.instance.sale_lines.exists():
            self.fields['item'].disabled = True
        style(self)

    def clean_item(self):
        item = self.cleaned_data['item']
        if EventStock.objects.filter(event=self.event, item=item).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This item already has a stock record for the event.')
        return item


class SaleForm(forms.Form):
    stock = forms.ModelChoiceField(queryset=EventStock.objects.none(), label='Item')
    quantity = forms.IntegerField(min_value=1)

    def __init__(self, *args, event, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        self.fields['stock'].queryset = EventStock.objects.filter(
            event=event, quantity__gt=0, item__is_active=True,
        ).select_related('item')
        self.fields['stock'].label_from_instance = (
            lambda stock: f'{stock.item.name} (₱{stock.item.unit_price} each, {stock.quantity} available)'
        )
        style(self)

    def clean(self):
        cleaned_data = super().clean()
        if self.event.status == Event.Status.CLOSED:
            raise ValidationError('Sales cannot be recorded for a closed event.')
        stock = cleaned_data.get('stock')
        quantity = cleaned_data.get('quantity')
        if stock and quantity and quantity > stock.quantity:
            self.add_error('quantity', 'Quantity exceeds the available event stock.')
        return cleaned_data