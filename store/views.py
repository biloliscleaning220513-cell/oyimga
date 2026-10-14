import hmac
import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import OrderForm, ReviewForm
from .models import Bonus, Order, Product

log = logging.getLogger('store')


def product_list(request):
    products = Product.objects.filter(is_active=True)
    bonuses = Bonus.objects.filter(is_active=True)
    return render(request, 'store/product_list.html', {'products': products, 'bonuses': bonuses})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    reviews = product.reviews.all()

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            try:
                review.full_clean()
                review.save()
                messages.success(request, "Fikringiz muvaffaqiyatli saqlandi!")
                return redirect('product_detail', pk=product.pk)
            except Exception as e:
                for error in e.messages if hasattr(e, 'messages') else [str(e)]:
                    messages.error(request, error)
        else:
            messages.error(request, "Iltimos, forma ma'lumotlarini to'g'ri to'ldiring.")
    else:
        form = ReviewForm()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
        'order_form': OrderForm(product=product),
    })


@require_POST
def product_order(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    form = OrderForm(request.POST, product=product)
    if form.is_valid():
        order = form.save(commit=False)
        order.product = product
        order.source = Order.SOURCE_SITE
        order.save()
        messages.success(request, f"Rahmat! Buyurtmangiz #{order.pk} qabul qilindi. Tez orada siz bilan bog'lanamiz.")
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect(reverse('product_detail', args=[product.pk]) + '#order')


@csrf_exempt
@require_POST
def telegram_webhook(request, secret):
    """Telegram yangilanishlarini qabul qiladi — bot sayt bilan bitta jarayonda va bitta bazada ishlaydi."""
    from telebot import types
    from .telegram_bot import get_bot

    expected = settings.TELEGRAM_WEBHOOK_SECRET
    header = request.headers.get('X-Telegram-Bot-Api-Secret-Token', '')
    if not (hmac.compare_digest(secret, expected) and hmac.compare_digest(header, expected)):
        raise Http404
    bot = get_bot()
    if bot:
        try:
            update = types.Update.de_json(request.body.decode('utf-8'))
            bot.process_new_updates([update])
        except Exception:
            log.exception("Telegram update xatosi")
    return HttpResponse('ok')
