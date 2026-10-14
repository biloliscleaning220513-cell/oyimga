from django.core.management.base import BaseCommand, CommandError

from store.telegram_bot import get_bot


class Command(BaseCommand):
    help = "Telegram botni polling rejimida ishga tushiradi (lokal kompyuter uchun)"

    def handle(self, *args, **options):
        bot = get_bot()
        if not bot:
            raise CommandError("TELEGRAM_BOT_TOKEN o'rnatilmagan")
        bot.remove_webhook()
        self.stdout.write(self.style.SUCCESS(f"Bot ishga tushdi: @{bot.get_me().username}"))
        bot.infinity_polling(skip_pending=True)
