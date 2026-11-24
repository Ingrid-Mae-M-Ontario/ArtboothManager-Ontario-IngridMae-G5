from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Item(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        constraints = [models.UniqueConstraint(fields=['owner', 'name'], name='unique_item_per_owner')]

    def __str__(self):
        return self.name


class Event(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned'
        ONGOING = 'ONGOING', 'Ongoing'
        CLOSED = 'CLOSED', 'Closed'

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='events')
    assistants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='assigned_events',
        limit_choices_to={'role': 'ASSISTANT'},
    )
    name = models.CharField(max_length=150)
    venue = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PLANNED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        constraints = [
            models.CheckConstraint(condition=models.Q(end_date__gte=models.F('start_date')), name='event_end_after_start'),
        ]

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be earlier than the start date.')

    def __str__(self):
        return self.name


class EventInventory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='event_stock')
    starting_qty = models.PositiveIntegerField()
    current_qty = models.PositiveIntegerField()

    class Meta:
        ordering = ['item__name']
        constraints = [models.UniqueConstraint(fields=['event', 'item'], name='unique_item_per_event')]

    def __str__(self):
        return f'{self.item} @ {self.event}'


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        E_WALLET = 'E_WALLET', 'E-Wallet'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Completed'
        VOIDED = 'VOIDED', 'Voided'

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='sales')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='sales_recorded')
    sale_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-sale_date']

    def __str__(self):
        return f'Sale #{self.pk}'


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    inventory = models.ForeignKey(EventInventory, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['sale', 'inventory'], name='unique_item_per_sale'),
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name='sale_item_qty_min_1'),
        ]

    @property
    def line_total(self):
        return self.quantity * self.unit_price