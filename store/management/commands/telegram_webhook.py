from django.conf import settings
from telebot.types import BotCommand
from django.core.management.base import BaseCommand
from django.urls import reverse

from store.telegram_bot import get_bot


class Command(BaseCommand):
    help = "Telegram webhookni sayt manziliga o'rnatadi (serverda bot sayt ichida ishlaydi)"

    def handle(self, *args, **options):
        bot = get_bot()
        if not bot:
            self.stdout.write("TELEGRAM_BOT_TOKEN yo'q — bot o'tkazib yuborildi")
            return
        if not settings.SITE_URL.startswith('https://'):
            self.stdout.write("SITE_URL https:// bilan boshlanmaydi — webhook o'rnatilmadi")
            return
        url = settings.SITE_URL + reverse('telegram_webhook', args=[settings.TELEGRAM_WEBHOOK_SECRET])
        bot.set_webhook(url=url, secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
                        allowed_updates=['message', 'callback_query'])
        bot.set_my_commands([
            BotCommand('start', 'Bosh menyu'),
            BotCommand('products', 'Mahsulotlar'),
        ])
        self.stdout.write(self.style.SUCCESS("Webhook o'rnatildi"))
