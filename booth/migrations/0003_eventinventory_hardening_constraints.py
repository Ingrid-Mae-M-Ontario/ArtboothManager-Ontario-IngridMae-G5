from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booth', '0002_eventinventory_sale_saleitem_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='eventinventory',
            constraint=models.CheckConstraint(
                condition=models.Q(('starting_qty__gte', 1)),
                name='event_inventory_start_min_1',
            ),
        ),
        migrations.AddConstraint(
            model_name='eventinventory',
            constraint=models.CheckConstraint(
                condition=models.Q(current_qty__lte=models.F('starting_qty')),
                name='event_inventory_current_lte_start',
            ),
        ),
    ]
