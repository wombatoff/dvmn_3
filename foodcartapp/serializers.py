from django.db import transaction
from rest_framework import serializers

from .models import Order, Product, OrderProduct
from .utils import fetch_coordinates


class OrderProductSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=True)
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)

    class Meta:
        model = OrderProduct
        fields = ('product', 'quantity', 'price')


class OrderSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(required=True)
    lastname = serializers.CharField(required=True)
    phonenumber = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    products = OrderProductSerializer(many=True, source='order_products', required=True)
    total_cost = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'firstname', 'lastname', 'phonenumber', 'address', 'products', 'total_cost')
        read_only_fields = ('total_cost',)

    @transaction.atomic
    def create(self, validated_data):
        order_products = validated_data.pop('order_products')
        order_coordinates = fetch_coordinates(validated_data['address'])
        if order_coordinates:
            longitude, latitude = order_coordinates
            order = Order.objects.create(latitude=latitude, longitude=longitude, **validated_data)
        else:
            order = Order.objects.create(**validated_data)

        for order_product in order_products:
            product = order_product['product']
            OrderProduct.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=order_product['quantity']
            )
        return order
