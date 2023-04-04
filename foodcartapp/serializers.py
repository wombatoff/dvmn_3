from rest_framework import serializers
from .models import Order, Product, OrderProduct


class OrderProductWriteSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderWriteSerializer(serializers.ModelSerializer):
    products = OrderProductWriteSerializer(many=True)

    class Meta:
        model = Order
        fields = ('firstname', 'lastname', 'phonenumber', 'address', 'products')

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for product_data in products_data:
            OrderProduct.objects.create(order=order, **product_data)
        return order


class OrderReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'firstname', 'lastname', 'phonenumber', 'address')
