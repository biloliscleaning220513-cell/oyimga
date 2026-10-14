from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Order, Product
from .telegram_bot import in_background, notify_new_order, post_to_channel


@receiver(post_save, sender=Product)
def product_created(sender, instance, created, **kwargs):
    # Admin paneldan yoki botdan qo'shilgan yangi mahsulot Telegram kanalga ham chiqadi
    if created and instance.is_active:
        transaction.on_commit(lambda: in_background(post_to_channel, instance))


@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    # Botdan kelgan buyurtmalar haqida bot o'zi xabar beradi
    if created and instance.source == Order.SOURCE_SITE:
        transaction.on_commit(lambda: in_background(notify_new_order, instance))
