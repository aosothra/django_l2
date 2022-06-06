from collections import defaultdict
from django.db import models
from django.db.models import Sum, F
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
        db_index=True
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItemQuerySet(models.QuerySet):
    def get_restaurants_with_items(self):
        '''Build associative dictionary with restaurants
        and corresponding list of products
        '''
        restaurants_with_items = defaultdict(list)

        restaurants_with_items_query = (
            self.select_related('restaurant')
            .select_related('product')
            .filter(availability=True)
        )

        for entry in restaurants_with_items_query:
            restaurants_with_items[entry.restaurant].append(entry.product.id)

        return restaurants_with_items


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    objects = RestaurantMenuItemQuerySet().as_manager()

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def annotate_price_total(self):
        return self.annotate(price_total=Sum(F('items__price') * F('items__quantity')))


class Order(models.Model):
    class Status(models.IntegerChoices):
        NEW = 0, _('Необработанный')
        CONFIRMED = 1, _('Обработанный')
        CANCELED = 2, _('Отмененный')
        FULFILLED = 3, _('Исполненный')
    
    class PaymentMethod(models.IntegerChoices):
        NOT_SELECTED = 0, _('Не выбрано')
        CASH = 1, _('Наличные')
        ONLINE = 2, _('Электронная')

    firstname = models.CharField(
        'Имя',
        max_length=40
    )
    lastname = models.CharField(
        'Фамилия',
        max_length=40
    )
    phonenumber = PhoneNumberField(
        'Номер телефона',
        db_index=True
    )
    address = models.CharField(
        'Адрес',
        max_length=200,
        db_index=True
    )
    status = models.SmallIntegerField(
        'Статус заказа',
        choices=Status.choices,
        default=Status.NEW,
        db_index=True
    )
    payment_method = models.SmallIntegerField(
        'Способ оплаты',
        choices=PaymentMethod.choices,
        default=PaymentMethod.NOT_SELECTED,
        db_index=True
    )
    assigned_restaurant = models.ForeignKey(
        Restaurant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Готовится в ресторане',
        related_name='orders'
    )
    note = models.TextField(
        'Комментарий',
        blank=True
    )
    created_on = models.DateTimeField(
        'Дата/время создания',
        null=False,
        default=timezone.now,
        db_index=True
    )
    confirmed_on = models.DateTimeField(
        'Дата/время подтверждения',
        null=True,
        blank=True,
        db_index=True
    )
    fulfilled_on = models.DateTimeField(
        'Дата/время исполнения',
        null=True,
        blank=True,
        db_index=True
    )

    objects = OrderQuerySet().as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.phonenumber}, {self.address}'


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар',
        related_name='demands'
    )

    price = models.DecimalField(
        'цена за шт',        
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    quantity = models.SmallIntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        verbose_name='Заказ',
        related_name='items'
    )

    def set_relevant_price(self):
        self.price = self.product.price
        return self

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции в заказе'

    def __str__(self):
        return f'{self.product.name} - {self.quantity} шт.'
