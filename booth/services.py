from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from booth.models import Event, EventStock, Sale, SaleLine


@transaction.atomic
def record_sale(*, event_id, stock_id, quantity, actor):
    event = Event.objects.select_for_update().get(pk=event_id)
    if event.status == Event.Status.CLOSED:
        raise ValidationError('Sales cannot be recorded for a closed event.')
    if event.owner_id != actor.pk and (
        actor.role != 'ASSISTANT' or not event.assistants.filter(pk=actor.pk).exists()
    ):
        raise ValidationError('You are not assigned to this event.')

    try:
        stock = EventStock.objects.select_for_update().select_related('item').get(
            pk=stock_id, event=event,
        )
    except EventStock.DoesNotExist as error:
        raise ValidationError('Selected stock does not belong to this event.') from error
    if not stock.item.is_active:
        raise ValidationError('This item is inactive and cannot be sold.')
    if quantity < 1:
        raise ValidationError('Sale quantity must be at least one.')
    if quantity > stock.quantity:
        raise ValidationError('Quantity exceeds the available event stock.')

    sale = Sale.objects.create(event=event, recorded_by=actor)
    SaleLine.objects.create(
        sale=sale,
        stock=stock,
        item_name=stock.item.name,
        quantity=quantity,
        unit_price=stock.item.unit_price,
    )
    EventStock.objects.filter(pk=stock.pk).update(quantity=F('quantity') - quantity)
    return sale


@transaction.atomic
def void_sale(*, sale_id, actor):
    sale = Sale.objects.select_for_update().select_related('event').get(pk=sale_id)
    is_owner = sale.event.owner_id == actor.pk
    is_recorder = (
        sale.recorded_by_id == actor.pk
        and actor.role == 'ASSISTANT'
        and sale.event.assistants.filter(pk=actor.pk).exists()
    )
    if not is_owner and not is_recorder:
        raise ValidationError('You do not have permission to void this sale.')
    if sale.status == Sale.Status.VOID:
        raise ValidationError('This sale has already been voided.')

    for line in sale.lines.select_related('stock').all():
        stock = EventStock.objects.select_for_update().get(pk=line.stock_id)
        EventStock.objects.filter(pk=stock.pk).update(quantity=F('quantity') + line.quantity)

    sale.status = Sale.Status.VOID
    sale.voided_by = actor
    sale.voided_at = timezone.now()
    sale.save(update_fields=['status', 'voided_by', 'voided_at'])
    return sale
