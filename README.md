# Kelin ko'ylaklari — sayt + Telegram bot

Sayt va Telegram bot **bitta bazadan** foydalanadi va bir vaqtda ishlaydi:

- Admin paneldan qo'shilgan mahsulot darhol saytda va botda chiqadi (kanal ulangan bo'lsa, kanalga ham joylanadi).
- Botdan qo'shilgan mahsulot (adminlar uchun «➕ Mahsulot qo'shish») darhol saytda chiqadi.
- Saytdan ham, botdan ham kelgan buyurtmalar bitta «Buyurtmalar» ro'yxatiga tushadi va adminlarga Telegramda xabar keladi
  (✅ Qabul qilindi / ❌ Bekor / 🏁 Yakunlandi tugmalari bilan — mijozga ham avtomatik javob boradi).
- Botda «🙈 Yashirish (sotildi)» tugmasi mahsulotni saytdan ham yashiradi.

## Bosh sahifa

1. 21:6 nisbatdagi bosh rasm (admin → «Sayt sozlamalari» → «Bosh rasm»)
2. Bizning mahsulotlar
3. Bizning bonuslarimiz (admin → «Bonuslar»)
4. Pastda: telefon, Instagram, Telegram (admin → «Sayt sozlamalari»)

## Maxfiy admin panel

`/admin/` manzili **ishlamaydi** (404). Admin panel faqat `ADMIN_URL` muhit o'zgaruvchisida
ko'rsatilgan maxfiy manzilda ochiladi, masalan `https://saytingiz.uz/k7q-boshqaruv-x93m/`.
Saytda admin panelga hech qanday havola yo'q.

Manzilni bilish uchun: `python manage.py admin_url`

## Render sozlamalari (Environment)

| O'zgaruvchi | Nima uchun |
|---|---|
| `SECRET_KEY` | Uzun tasodifiy matn (majburiy) |
| `ADMIN_URL` | Maxfiy admin manzili, masalan `k7q-boshqaruv-x93m` (majburiy, hech kimga aytmang) |
| `TELEGRAM_BOT_TOKEN` | @BotFather bergan token |
| `TELEGRAM_ADMIN_IDS` | Buyurtma xabarlari keladigan Telegram ID lar, vergul bilan (ID ni bilish: botga `/id` yozing) |
| `TELEGRAM_CHANNEL_ID` | (ixtiyoriy) Yangi mahsulotlar joylanadigan kanal, masalan `@oyimga_kanal` — bot kanalda admin bo'lishi kerak |
| `SITE_URL` | (ixtiyoriy) Sayt manzili; Render'da avtomatik aniqlanadi |
| `DATABASE_URL` | (tavsiya) Render PostgreSQL manzili — aks holda `db.sqlite3` ishlatiladi |

Build Command: `./build.sh` — u bazani yangilaydi va Telegram webhookni avtomatik o'rnatadi.
Start Command: `gunicorn config.wsgi:application`

Bot alohida server talab qilmaydi — u sayt ichida (webhook orqali) ishlaydi, shuning uchun baza doim bitta.

> ⚠️ Render bepul tarifida diskka yozilgan fayllar (SQLite baza va yuklangan rasmlar) har deploy'da
> o'chib ketishi mumkin. Doimiy saqlash uchun Render PostgreSQL (`DATABASE_URL`) va
> Persistent Disk (`MEDIA_ROOT=/var/data/media`) ulang.

## Lokal ishga tushirish

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver          # sayt
python manage.py runbot             # bot (boshqa terminalda, TELEGRAM_BOT_TOKEN bilan)
python manage.py admin_url          # maxfiy admin manzili
```
