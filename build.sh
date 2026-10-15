#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
# Telegram botni sayt bilan ulaydi (TELEGRAM_BOT_TOKEN berilgan bo'lsa)
python manage.py telegram_webhook || echo "Webhook o'rnatilmadi"
