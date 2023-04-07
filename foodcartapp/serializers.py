from django.db import transaction
from rest_framework import serializers

from .models import Order, Product, OrderProduct
from .utils import create_order_restaurant_info


class OrderProductWriteSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)

    class Meta:
        model = OrderProduct
        fields = ('product', 'quantity', 'price')


class OrderWriteSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(required=True)
    lastname = serializers.CharField(required=True)
    phonenumber = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    products = OrderProductWriteSerializer(many=True)


    class Meta:
        model = Order
        fields = ('firstname', 'lastname', 'phonenumber', 'address', 'products')

    def validate_products(self, products):
        if not products:
            raise serializers.ValidationError("Список продуктов не может быть пустым.")
        return products

    @transaction.atomic
    def create(self, validated_data):
        order_products = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for order_product in order_products:
            product = order_product['product']
            OrderProduct.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=order_product['quantity']
            )

        create_order_restaurant_info(order)

        return order


class OrderReadSerializer(serializers.ModelSerializer):
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ('id', 'firstname', 'lastname', 'phonenumber', 'address', 'total_cost')

    def get_total_cost(self, obj):
        total_cost = 0
        order_products = OrderProduct.objects.filter(order=obj)
        for order_product in order_products:
            total_cost += order_product.price * order_product.quantity
        return total_cost
