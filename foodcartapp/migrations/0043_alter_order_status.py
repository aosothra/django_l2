# Generated by Django 3.2 on 2022-05-16 14:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0042_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.SmallIntegerField(choices=[(0, 'Необработанный'), (1, 'Обработанный'), (2, 'Отмененный')], db_index=True, default=0, verbose_name='Статус заказа'),
        ),
    ]