"""
Telegram bot. Sayt bilan BITTA bazadan (Django modellari orqali) foydalanadi:
admin paneldan qo'shilgan mahsulot darhol botda, botdan qo'shilgani darhol saytda ko'rinadi.

Ishga tushirish:
  * Serverda (Render): webhook — /tg/<TELEGRAM_WEBHOOK_SECRET>/ manzili orqali,
    `python manage.py telegram_webhook` buyrug'i webhookni o'rnatadi.
  * Lokal kompyuterda: `python manage.py runbot` (polling).
"""
import html
import logging
import threading
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.files.base import ContentFile

import telebot
from telebot import types

from .models import BotState, Bonus, Order, Product, SiteSettings

log = logging.getLogger('store')

PAGE_SIZE = 5
BTN_PRODUCTS = "👗 Mahsulotlar"
BTN_BONUSES = "🎁 Bonuslar"
BTN_CONTACT = "📞 Aloqa"
BTN_CANCEL = "❌ Bekor qilish"

_bot = None
_lock = threading.Lock()


def esc(text):
    return html.escape(text, quote=False)


def get_bot():
    global _bot
    if not settings.TELEGRAM_BOT_TOKEN:
        return None
    with _lock:
        if _bot is None:
            _bot = telebot.TeleBot(settings.TELEGRAM_BOT_TOKEN, parse_mode='HTML', threaded=False)
            _register(_bot)
    return _bot


def is_admin(user_id):
    return user_id in settings.TELEGRAM_ADMIN_IDS


def fmt_price(value):
    return f"{int(value):,}".replace(',', ' ') + " so'm"


def product_url(product):
    if settings.SITE_URL.startswith('https://'):
        return f"{settings.SITE_URL}/product/{product.pk}/"
    return ''


# ---------------------------------------------------------------- holat (state)

def get_state(chat_id):
    return BotState.objects.filter(chat_id=chat_id).first()


def set_state(chat_id, step, data):
    BotState.objects.update_or_create(chat_id=chat_id, defaults={'step': step, 'data': data})


def clear_state(chat_id):
    BotState.objects.filter(chat_id=chat_id).delete()


# ---------------------------------------------------------------- yuborish

def main_menu(user_id=None):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(BTN_PRODUCTS)
    kb.row(BTN_BONUSES, BTN_CONTACT)
    if user_id and is_admin(user_id):
        kb.row("➕ Mahsulot qo'shish", "📋 Buyurtmalar")
    return kb


def cancel_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(BTN_CANCEL)
    return kb


def product_caption(p):
    lines = [f"<b>{esc(p.name)}</b>", f"💰 {fmt_price(p.price)}"]
    if p.size_list:
        lines.append(f"📏 O'lchamlar: {esc(', '.join(p.size_list))}")
    if p.description:
        lines.append('')
        lines.append(esc(p.description))
    text = '\n'.join(lines)
    return text if len(text) <= 1000 else text[:997] + '...'


def product_markup(p, admin=False):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛒 Buyurtma berish", callback_data=f"order:{p.pk}"))
    url = product_url(p)
    if url:
        kb.add(types.InlineKeyboardButton("🌐 Saytda ko'rish", url=url))
    if admin:
        kb.add(types.InlineKeyboardButton("🙈 Yashirish (sotildi)", callback_data=f"hide:{p.pk}"))
    return kb


def send_product(bot, chat_id, p, admin=False, markup=True):
    caption = product_caption(p)
    kb = product_markup(p, admin) if markup else None
    if p.telegram_file_id:
        try:
            return bot.send_photo(chat_id, p.telegram_file_id, caption=caption, reply_markup=kb)
        except Exception:
            log.warning("file_id eskirgan, rasm qayta yuklanadi: %s", p.pk)
    if p.image:
        try:
            with p.image.open('rb') as f:
                msg = bot.send_photo(chat_id, f, caption=caption, reply_markup=kb)
            Product.objects.filter(pk=p.pk).update(telegram_file_id=msg.photo[-1].file_id)
            return msg
        except Exception:
            log.exception("Rasm yuborilmadi: %s", p.pk)
    return bot.send_message(chat_id, caption, reply_markup=kb)


def send_products(bot, chat_id, user_id, offset=0):
    qs = Product.objects.filter(is_active=True)
    total = qs.count()
    if not total:
        bot.send_message(chat_id, "Hozircha mahsulotlar yo'q. Tez orada qo'shiladi! 🌸")
        return
    for p in qs[offset:offset + PAGE_SIZE]:
        send_product(bot, chat_id, p, admin=is_admin(user_id))
    nxt = offset + PAGE_SIZE
    if nxt < total:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(f"⬇️ Yana ko'rsatish ({total - nxt})", callback_data=f"more:{nxt}"))
        bot.send_message(chat_id, f"{nxt} / {total}", reply_markup=kb)


def order_text(order):
    product = order.product.name if order.product else "—"
    src = "🌐 Sayt" if order.source == Order.SOURCE_SITE else "🤖 Telegram bot"
    lines = [
        f"🛍 <b>Yangi buyurtma #{order.pk}</b> ({src})",
        f"👗 {esc(product)}" + (f" — {fmt_price(order.product.price)}" if order.product else ''),
    ]
    if order.size:
        lines.append(f"📏 O'lcham: {esc(order.size)}")
    lines.append(f"👤 {esc(order.customer_name)}")
    lines.append(f"📞 {esc(order.phone)}")
    if order.note:
        lines.append(f"💬 {esc(order.note)}")
    if order.telegram_user_id:
        lines.append(f'✉️ <a href="tg://user?id={order.telegram_user_id}">Mijozga yozish</a>')
    lines.append(f"Holati: {order.get_status_display()}")
    return '\n'.join(lines)


def order_admin_markup(order):
    kb = types.InlineKeyboardMarkup()
    kb.row(
        types.InlineKeyboardButton("✅ Qabul qilindi", callback_data=f"st:{order.pk}:accepted"),
        types.InlineKeyboardButton("❌ Bekor", callback_data=f"st:{order.pk}:cancelled"),
    )
    kb.row(types.InlineKeyboardButton("🏁 Yakunlandi", callback_data=f"st:{order.pk}:done"))
    return kb


def notify_new_order(order):
    """Yangi buyurtma haqida barcha adminlarga xabar yuboradi."""
    bot = get_bot()
    if not bot:
        return
    for admin_id in settings.TELEGRAM_ADMIN_IDS:
        try:
            bot.send_message(admin_id, order_text(order), reply_markup=order_admin_markup(order))
        except Exception:
            log.exception("Adminga xabar yuborilmadi: %s", admin_id)


def post_to_channel(product):
    """Yangi mahsulotni Telegram kanalga joylaydi (TELEGRAM_CHANNEL_ID berilgan bo'lsa)."""
    bot = get_bot()
    if not bot or not settings.TELEGRAM_CHANNEL_ID:
        return
    try:
        product = Product.objects.get(pk=product.pk)
        caption = product_caption(product)
        kb = types.InlineKeyboardMarkup()
        bot_username = SiteSettings.load().telegram_bot
        if bot_username:
            kb.add(types.InlineKeyboardButton(
                "🛒 Buyurtma berish",
                url=f"https://t.me/{SiteSettings._username(bot_username)}?start=p{product.pk}",
            ))
        url = product_url(product)
        if url:
            kb.add(types.InlineKeyboardButton("🌐 Saytda ko'rish", url=url))
        kb = kb if kb.keyboard else None
        if product.image:
            with product.image.open('rb') as f:
                bot.send_photo(settings.TELEGRAM_CHANNEL_ID, f, caption=caption, reply_markup=kb)
        else:
            bot.send_message(settings.TELEGRAM_CHANNEL_ID, caption, reply_markup=kb)
    except Exception:
        log.exception("Kanalga joylanmadi: %s", product.pk)


def in_background(func, *args):
    """Saytni sekinlashtirmaslik uchun Telegramga yuborishni alohida oqimda bajaradi."""
    if settings.TELEGRAM_BOT_TOKEN:
        threading.Thread(target=func, args=args, daemon=True).start()


# ---------------------------------------------------------------- handlerlar

def _register(bot):

    def start_order(chat_id, product):
        set_state(chat_id, 'order_name', {'product_id': product.pk})
        bot.send_message(
            chat_id,
            f"🛒 <b>{esc(product.name)}</b> uchun buyurtma.\n\nIsmingizni yozing:",
            reply_markup=cancel_menu(),
        )

    @bot.message_handler(commands=['start'])
    def cmd_start(m):
        clear_state(m.chat.id)
        site = SiteSettings.load()
        bot.send_message(
            m.chat.id,
            f"Assalomu alaykum! 🌸\n<b>{esc(site.site_name)}</b> botiga xush kelibsiz.\n\n"
            "Bu yerda kelinlik ko'ylaklarimizni ko'rib, buyurtma berishingiz mumkin.",
            reply_markup=main_menu(m.from_user.id),
        )
        # Sayt yoki kanaldagi "Buyurtma" tugmasidan kelgan bo'lsa: /start p<id>
        parts = m.text.split(maxsplit=1)
        if len(parts) == 2 and parts[1].startswith('p') and parts[1][1:].isdigit():
            p = Product.objects.filter(pk=int(parts[1][1:]), is_active=True).first()
            if p:
                send_product(bot, m.chat.id, p, admin=is_admin(m.from_user.id))

    @bot.message_handler(commands=['cancel'])
    @bot.message_handler(func=lambda m: m.text == BTN_CANCEL)
    def cmd_cancel(m):
        clear_state(m.chat.id)
        bot.send_message(m.chat.id, "Bekor qilindi.", reply_markup=main_menu(m.from_user.id))

    @bot.message_handler(commands=['id'])
    def cmd_id(m):
        bot.send_message(m.chat.id, f"Sizning Telegram ID: <code>{m.from_user.id}</code>")

    @bot.message_handler(commands=['add'])
    @bot.message_handler(func=lambda m: m.text == "➕ Mahsulot qo'shish")
    def cmd_add(m):
        if not is_admin(m.from_user.id):
            return
        set_state(m.chat.id, 'add_photo', {})
        bot.send_message(m.chat.id, "📸 Mahsulot rasmini yuboring:", reply_markup=cancel_menu())

    @bot.message_handler(commands=['orders'])
    @bot.message_handler(func=lambda m: m.text == "📋 Buyurtmalar")
    def cmd_orders(m):
        if not is_admin(m.from_user.id):
            return
        orders = list(Order.objects.select_related('product')[:10])
        if not orders:
            bot.send_message(m.chat.id, "Hozircha buyurtmalar yo'q.")
        for o in reversed(orders):
            bot.send_message(m.chat.id, order_text(o).replace("Yangi buyurtma", "Buyurtma"),
                             reply_markup=order_admin_markup(o))

    @bot.message_handler(func=lambda m: m.text == BTN_PRODUCTS)
    @bot.message_handler(commands=['products'])
    def cmd_products(m):
        send_products(bot, m.chat.id, m.from_user.id)

    @bot.message_handler(func=lambda m: m.text == BTN_BONUSES)
    def cmd_bonuses(m):
        bonuses = Bonus.objects.filter(is_active=True)
        if not bonuses:
            bot.send_message(m.chat.id, "Bonuslar tez orada e'lon qilinadi! 🎁")
            return
        text = "🎁 <b>Bizning bonuslarimiz</b>\n\n" + '\n\n'.join(
            f"{b.icon} <b>{esc(b.title)}</b>\n{esc(b.description)}" for b in bonuses
        )
        bot.send_message(m.chat.id, text)

    @bot.message_handler(func=lambda m: m.text == BTN_CONTACT)
    def cmd_contact(m):
        s = SiteSettings.load()
        lines = ["📞 <b>Biz bilan bog'laning</b>", '']
        if s.phone:
            lines.append(f"☎️ {esc(s.phone)}")
        if s.instagram_url:
            lines.append(f"📷 Instagram: {s.instagram_url}")
        if s.telegram_url:
            lines.append(f"✈️ Telegram: {s.telegram_url}")
        if s.address:
            lines.append(f"📍 {esc(s.address)}")
        if settings.SITE_URL.startswith('http'):
            lines.append(f"🌐 Sayt: {settings.SITE_URL}")
        bot.send_message(m.chat.id, '\n'.join(lines), disable_web_page_preview=True)

    # ---- callback tugmalar
    @bot.callback_query_handler(func=lambda c: True)
    def on_callback(c):
        chat_id = c.message.chat.id
        action, _, arg = c.data.partition(':')
        if action == 'more':
            bot.answer_callback_query(c.id)
            send_products(bot, chat_id, c.from_user.id, int(arg))
        elif action == 'order':
            p = Product.objects.filter(pk=int(arg), is_active=True).first()
            bot.answer_callback_query(c.id, None if p else "Bu mahsulot endi mavjud emas")
            if p:
                start_order(chat_id, p)
        elif action == 'hide' and is_admin(c.from_user.id):
            Product.objects.filter(pk=int(arg)).update(is_active=False)
            bot.answer_callback_query(c.id, "Yashirildi — saytda ham ko'rinmaydi")
        elif action == 'st' and is_admin(c.from_user.id):
            pk, _, status = arg.partition(':')
            order = Order.objects.select_related('product').filter(pk=int(pk)).first()
            if not order or status not in dict(Order.STATUS_CHOICES):
                bot.answer_callback_query(c.id, "Topilmadi")
                return
            order.status = status
            order.save(update_fields=['status'])
            bot.answer_callback_query(c.id, order.get_status_display())
            try:
                bot.edit_message_text(order_text(order), chat_id, c.message.message_id,
                                      reply_markup=order_admin_markup(order))
            except Exception:
                pass
            if order.telegram_user_id and status in ('accepted', 'cancelled'):
                msg = ("✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog'lanamiz."
                       if status == 'accepted' else "Buyurtmangiz bekor qilindi.")
                try:
                    bot.send_message(order.telegram_user_id, f"Buyurtma #{order.pk}: {msg}")
                except Exception:
                    pass
        else:
            bot.answer_callback_query(c.id)

    # ---- bosqichma-bosqich suhbat (buyurtma va mahsulot qo'shish)
    @bot.message_handler(content_types=['text', 'contact', 'photo'])
    def on_message(m):
        state = get_state(m.chat.id)
        if not state:
            bot.send_message(m.chat.id, "Quyidagi menyudan tanlang 👇", reply_markup=main_menu(m.from_user.id))
            return
        data = state.data
        step = state.step
        text = (m.text or '').strip()

        # --- Buyurtma
        if step == 'order_name':
            if not text:
                bot.send_message(m.chat.id, "Ismingizni matn ko'rinishida yozing:")
                return
            data['name'] = text[:100]
            set_state(m.chat.id, 'order_phone', data)
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.row(types.KeyboardButton("📱 Raqamni yuborish", request_contact=True))
            kb.row(BTN_CANCEL)
            bot.send_message(m.chat.id, "Telefon raqamingizni yuboring yoki yozing:", reply_markup=kb)

        elif step == 'order_phone':
            phone = m.contact.phone_number if m.contact else text
            if sum(ch.isdigit() for ch in phone) < 7:
                bot.send_message(m.chat.id, "Telefon raqam noto'g'ri. Qaytadan kiriting:")
                return
            data['phone'] = phone[:30]
            product = Product.objects.filter(pk=data['product_id']).first()
            if product and product.size_list:
                set_state(m.chat.id, 'order_size', data)
                kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
                kb.add(*product.size_list)
                kb.row("Bilmayman")
                kb.row(BTN_CANCEL)
                bot.send_message(m.chat.id, "📏 O'lchamni tanlang:", reply_markup=kb)
            else:
                finish_order(m, data)

        elif step == 'order_size':
            data['size'] = '' if text == "Bilmayman" else text[:20]
            finish_order(m, data)

        # --- Mahsulot qo'shish (faqat adminlar)
        elif step.startswith('add_') and not is_admin(m.from_user.id):
            clear_state(m.chat.id)

        elif step == 'add_photo':
            if not m.photo:
                bot.send_message(m.chat.id, "Iltimos, rasm yuboring 📸")
                return
            data['file_id'] = m.photo[-1].file_id
            set_state(m.chat.id, 'add_name', data)
            bot.send_message(m.chat.id, "✏️ Mahsulot nomini yozing:")

        elif step == 'add_name':
            if not text:
                return
            data['name'] = text[:200]
            set_state(m.chat.id, 'add_price', data)
            bot.send_message(m.chat.id, "💰 Narxini yozing (faqat raqam, masalan 3500000):")

        elif step == 'add_price':
            try:
                price = Decimal(''.join(ch for ch in text if ch.isdigit() or ch == '.'))
            except InvalidOperation:
                bot.send_message(m.chat.id, "Narx noto'g'ri. Faqat raqam yozing:")
                return
            data['price'] = str(price)
            set_state(m.chat.id, 'add_sizes', data)
            bot.send_message(m.chat.id, "📏 O'lchamlarni vergul bilan yozing (masalan: 40, 42, 44) yoki «-» yuboring:")

        elif step == 'add_sizes':
            data['sizes'] = '' if text == '-' else text[:100]
            set_state(m.chat.id, 'add_desc', data)
            bot.send_message(m.chat.id, "📝 Tavsif yozing yoki «-» yuboring:")

        elif step == 'add_desc':
            product = Product(
                name=data['name'],
                price=Decimal(data['price']),
                sizes=data.get('sizes', ''),
                description='' if text == '-' else text,
            )
            try:
                file_info = bot.get_file(data['file_id'])
                content = bot.download_file(file_info.file_path)
                product.image.save(f"tg_{data['file_id'][-12:]}.jpg", ContentFile(content), save=False)
                product.telegram_file_id = data['file_id']
            except Exception:
                log.exception("Rasm yuklab olinmadi")
            product.save()
            clear_state(m.chat.id)
            bot.send_message(m.chat.id, "✅ Mahsulot qo'shildi! U saytda ham darhol ko'rinadi.",
                             reply_markup=main_menu(m.from_user.id))
            send_product(bot, m.chat.id, product, admin=True)

    def finish_order(m, data):
        product = Product.objects.filter(pk=data['product_id']).first()
        order = Order.objects.create(
            product=product,
            customer_name=data['name'],
            phone=data['phone'],
            size=data.get('size', ''),
            source=Order.SOURCE_TELEGRAM,
            telegram_user_id=m.from_user.id,
        )
        clear_state(m.chat.id)
        bot.send_message(
            m.chat.id,
            f"✅ Rahmat! Buyurtmangiz #{order.pk} qabul qilindi.\nTez orada siz bilan bog'lanamiz. 🌸",
            reply_markup=main_menu(m.from_user.id),
        )
        notify_new_order(order)
