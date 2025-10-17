
import uuid
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Order, OrderItem, CartItem


@receiver(pre_save, sender=Order)
def generate_order_id(sender, instance, **kwargs):
    if not instance.order_id:
        instance.order_id = f"ORD-{uuid.uuid4().hex[:10].upper()}"


@receiver(post_save, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    order = instance.order
    total = sum(item.price * item.quantity for item in order.items.all())
    order.total = total
    order.save(update_fields=['total'])


@receiver(post_save, sender=OrderItem)
def clear_cart_item(sender, instance, **kwargs):
    CartItem.objects.filter(user=instance.order.user, product=instance.product).delete()
