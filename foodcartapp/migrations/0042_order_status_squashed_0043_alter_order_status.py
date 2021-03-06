# Generated by Django 3.2 on 2022-05-16 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('foodcartapp', '0042_order_status'), ('foodcartapp', '0043_alter_order_status')]

    dependencies = [
        ('foodcartapp', '0041_alter_orderitem_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Необработанный'), (1, 'Обработанный'), (2, 'Отмененный')], db_index=True, default=0, verbose_name='Статус заказа'),
        ),
    ]
