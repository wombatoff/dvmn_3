from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Sum
from django.utils import timezone
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
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="широта"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="долгота"
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
        indexes = [
            models.Index(fields=['name'], name='name_idx'),
        ]

    def __str__(self):
        return self.name


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

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            total_cost=Sum(F('order_products__quantity') * F('order_products__product__price'))
        )


NEW = 'новый'
MANAGER_REVIEW = 'подтверждение менеджером'
RESTAURANT_PROCESSING = 'обработка рестораном'
COURIER_DELIVERY = 'доставка курьером'
COMPLETED = 'завершен'

ONLINE_PAYMENT = 'электронно'
CASH_PAYMENT = 'наличными'


class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        (NEW, NEW),
        (MANAGER_REVIEW, MANAGER_REVIEW),
        (RESTAURANT_PROCESSING, RESTAURANT_PROCESSING),
        (COURIER_DELIVERY, COURIER_DELIVERY),
        (COMPLETED, COMPLETED),
    ]
    status = models.CharField(
        max_length=36,
        choices=ORDER_STATUS_CHOICES,
        default=NEW,
        verbose_name='статус заказа',
    )
    PAYMENT_CHOICES = [
        (ONLINE_PAYMENT, ONLINE_PAYMENT),
        (CASH_PAYMENT, CASH_PAYMENT),
    ]
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        blank=True,
        verbose_name='способ оплаты',
    )
    order_date = models.DateTimeField(
        default=timezone.now,
        verbose_name='дата заказа',
    )
    call_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='дата звонка',
    )
    delivery_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='дата доставки',
    )
    firstname = models.CharField(verbose_name='имя', max_length=50)

    lastname = models.CharField(verbose_name='фамилия', max_length=50)

    phonenumber = PhoneNumberField(verbose_name='телефон')
    address = models.CharField(verbose_name='адрес', max_length=100)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="широта"
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="долгота"
    )
    products = models.ManyToManyField(
        'Product',
        through='OrderProduct',
        verbose_name='продукты',
        related_name='products',
        blank=False,
    )
    comments = models.TextField(blank=True)
    assigned_restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='назначенный ресторан',
    )
    objects = OrderManager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'
        indexes = [
            models.Index(fields=['firstname', 'lastname'])
        ]

    def __str__(self):
        return f"{self.firstname} {self.lastname}"


class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        'количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        unique_together = ('order', 'product')
