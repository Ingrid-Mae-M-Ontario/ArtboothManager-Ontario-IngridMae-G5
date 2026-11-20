from django import forms
from django.core.exceptions import ValidationError

from accounts.models import User
from booth.models import Event, Item


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