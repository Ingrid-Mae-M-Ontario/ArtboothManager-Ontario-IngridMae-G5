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


class EventStock(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='stock')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='event_stock')
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['item__name']
        constraints = [
            models.UniqueConstraint(fields=['event', 'item'], name='unique_item_stock_per_event'),
            models.CheckConstraint(condition=models.Q(quantity__gte=0), name='event_stock_nonnegative'),
        ]

    def clean(self):
        if self.event_id and self.item_id and self.event.owner_id != self.item.owner_id:
            raise ValidationError('Stock items must belong to the event owner.')

    def __str__(self):
        return f'{self.item.name} at {self.event.name}: {self.quantity}'


class Sale(models.Model):
    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Completed'
        VOID = 'VOID', 'Voided'

    event = models.ForeignKey(Event, on_delete=models.PROTECT, related_name='sales')
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='recorded_sales'
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    created_at = models.DateTimeField(auto_now_add=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='voided_sales', null=True, blank=True,
    )

    class Meta:
        ordering = ['-created_at']

    @property
    def total(self):
        return sum(
            (line.unit_price * line.quantity for line in self.lines.all()),
            Decimal('0.00'),
        )

    def __str__(self):
        return f'Sale #{self.pk} at {self.event.name}'


class SaleLine(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name='lines')
    stock = models.ForeignKey(EventStock, on_delete=models.PROTECT, related_name='sale_lines')
    item_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['sale', 'stock'], name='unique_stock_line_per_sale'),
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name='sale_line_quantity_positive'),
        ]

    @property
    def subtotal(self):
        return self.unit_price * self.quantity