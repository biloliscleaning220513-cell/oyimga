"""
Render uchun kirish nuqtasi: `gunicorn app:app`.

Render'da Build Command faqat `pip install -r requirements.txt` bo'lsa ham sayt ishlashi uchun
ishga tushishda bazani yangilaydi, static fayllarni yig'adi va Telegram webhookni o'rnatadi.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402

call_command('migrate', interactive=False, verbosity=1)
call_command('collectstatic', interactive=False, verbosity=0)
try:
    call_command('telegram_webhook')
except Exception as exc:  # bot ishlamasa ham sayt ochilaversin
    print(f"Telegram webhook o'rnatilmadi: {exc}")

from config.wsgi import application as app  # noqa: E402

application = app
