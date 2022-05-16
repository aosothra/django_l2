# Generated by Django 3.2 on 2022-05-13 18:15

from django.db import migrations


def set_backdate_order_prices(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')
    for order_item in OrderItem.objects.select_related('product').all().iterator():
        order_item.price = order_item.product.price
        order_item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0039_auto_20220513_1813'),
    ]

    operations = [
        migrations.RunPython(set_backdate_order_prices)
    ]
