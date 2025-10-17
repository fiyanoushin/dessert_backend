from rest_framework import serializers
from .models import User, Product, CartItem, WishlistItem, Order, OrderItem
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['id', 'username', 'name', 'email', 'role', 'isBlocked']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = UserModel
        fields = ['username', 'email', 'password', 'name', 'role']

    def create(self, validated_data):
        username = validated_data.get('username') or validated_data['email'].split('@')[0]
        user = UserModel.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name', ''),
            role=validated_data.get('role', 'user')
        )
        return user


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_detail', 'quantity']
        extra_kwargs = {'product': {'write_only': True}}

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product']
        qty = validated_data.get('quantity', 1)
        obj, created = CartItem.objects.get_or_create(user=user, product=product)
        if not created:
            obj.quantity += qty
        else:
            obj.quantity = qty
        obj.save()
        return obj

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get('quantity', instance.quantity)
        instance.save()
        return instance


class WishlistItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_detail']
        extra_kwargs = {'product': {'write_only': True}}

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product']
        obj, created = WishlistItem.objects.get_or_create(user=user, product=product)
        return obj

class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_detail', 'quantity', 'price']

class OrderCreateItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField(min_value=1)

class OrderSerializer(serializers.ModelSerializer):
    items = OrderCreateItemSerializer(many=True, write_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True, source='items')

    class Meta:
        model = Order
        fields = ['id', 'order_id', 'user', 'total', 'status', 'payment_method', 'date', 'items', 'order_items']
        read_only_fields = ['user', 'total', 'status', 'date', 'order_items', 'order_id']

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        items_data = validated_data.pop('items')

        order = Order.objects.create(user=user, total=0, payment_method=validated_data.get('payment_method', 'COD'))

        total = 0
        order_items_objs = []
        for it in items_data:
            product = it['product']
            qty = it['quantity']
            price = product.price
            oi = OrderItem(order=order, product=product, quantity=qty, price=price)
            order_items_objs.append(oi)
            total += price * qty

        OrderItem.objects.bulk_create(order_items_objs)
        order.total = total
        order.save()
        return order
