from django.core.exceptions import ValidationError
from django.db import models


class SiteSettings(models.Model):
    """Sayt sozlamalari: bosh rasm, aloqa ma'lumotlari. Faqat bitta yozuv bo'ladi."""
    site_name = models.CharField(max_length=100, default="Kelin ko'ylaklari", verbose_name="Sayt nomi")
    hero_image = models.ImageField(
        upload_to='site/', blank=True, null=True,
        verbose_name="Bosh rasm (21:6)",
        help_text="Sayt boshida chiqadigan keng rasm. Tavsiya: 2100×600 yoki 4200×1200 piksel.",
    )
    hero_title = models.CharField(max_length=150, blank=True, default="Orzuingizdagi kelinlik libosi", verbose_name="Bosh rasm sarlavhasi")
    hero_subtitle = models.CharField(max_length=250, blank=True, default="Har bir ko'ylak — sizning eng baxtli kuningiz uchun", verbose_name="Bosh rasm matni")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Telefon raqam", help_text="Masalan: +998 90 123 45 67")
    instagram = models.CharField(max_length=100, blank=True, verbose_name="Instagram", help_text="Faqat username, masalan: oyimga_dress")
    telegram = models.CharField(max_length=100, blank=True, verbose_name="Telegram", help_text="Username (masalan: oyimga_admin) yoki kanal")
    telegram_bot = models.CharField(max_length=100, blank=True, verbose_name="Telegram bot username", help_text="Masalan: oyimga_bot")
    address = models.CharField(max_length=250, blank=True, verbose_name="Manzil")

    class Meta:
        verbose_name = "Sayt sozlamalari"
        verbose_name_plural = "Sayt sozlamalari"

    def __str__(self):
        return "Sayt sozlamalari"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @staticmethod
    def _username(value):
        return value.strip().rstrip('/').split('/')[-1].lstrip('@')

    @property
    def instagram_url(self):
        return f"https://instagram.com/{self._username(self.instagram)}" if self.instagram else ''

    @property
    def telegram_url(self):
        return f"https://t.me/{self._username(self.telegram)}" if self.telegram else ''

    @property
    def bot_url(self):
        return f"https://t.me/{self._username(self.telegram_bot)}" if self.telegram_bot else ''

    @property
    def phone_link(self):
        return ''.join(c for c in self.phone if c.isdigit() or c == '+')


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Narxi (so'm)")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Asosiy rasm")
    sizes = models.CharField(max_length=100, blank=True, verbose_name="O'lchamlar", help_text="Vergul bilan: 40, 42, 44, 46")
    is_active = models.BooleanField(default=True, verbose_name="Saytda va botda ko'rinsin")
    telegram_file_id = models.CharField(max_length=255, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Rasm almashtirilsa, Telegramdagi eski nusxani unutamiz
        if self.pk:
            old = Product.objects.filter(pk=self.pk).values_list('image', flat=True).first()
            if old != (self.image.name if self.image else ''):
                self.telegram_file_id = ''
        super().save(*args, **kwargs)

    @property
    def size_list(self):
        return [s.strip() for s in self.sizes.split(',') if s.strip()]


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Mahsulot")
    image = models.ImageField(upload_to='products/', verbose_name="Rasm")
    position = models.PositiveIntegerField(default=0, verbose_name="Tartib")

    class Meta:
        verbose_name = "Qo'shimcha rasm"
        verbose_name_plural = "Qo'shimcha rasmlar"
        ordering = ['position', 'id']


class Bonus(models.Model):
    icon = models.CharField(max_length=10, default='🎁', verbose_name="Belgi (emoji)")
    title = models.CharField(max_length=150, verbose_name="Sarlavha")
    description = models.TextField(blank=True, verbose_name="Tavsif")
    position = models.PositiveIntegerField(default=0, verbose_name="Tartib")
    is_active = models.BooleanField(default=True, verbose_name="Ko'rinsin")

    class Meta:
        verbose_name = "Bonus"
        verbose_name_plural = "Bonuslar"
        ordering = ['position', 'id']

    def __str__(self):
        return self.title


class Order(models.Model):
    SOURCE_SITE = 'site'
    SOURCE_TELEGRAM = 'telegram'
    SOURCE_CHOICES = [(SOURCE_SITE, 'Sayt'), (SOURCE_TELEGRAM, 'Telegram bot')]

    STATUS_NEW = 'new'
    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('accepted', 'Qabul qilindi'),
        ('done', 'Yakunlandi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name='orders', verbose_name="Mahsulot")
    customer_name = models.CharField(max_length=100, verbose_name="Mijoz ismi")
    phone = models.CharField(max_length=30, verbose_name="Telefon")
    size = models.CharField(max_length=20, blank=True, verbose_name="O'lcham")
    note = models.TextField(blank=True, verbose_name="Izoh")
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_SITE, verbose_name="Qayerdan")
    telegram_user_id = models.BigIntegerField(null=True, blank=True, verbose_name="Telegram ID")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_NEW, verbose_name="Holati")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Vaqti")

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} {self.customer_name}"


class BotState(models.Model):
    """Telegram botdagi suhbat bosqichi (buyurtma / mahsulot qo'shish)."""
    chat_id = models.BigIntegerField(unique=True)
    step = models.CharField(max_length=30)
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Mahsulot")
    client_name = models.CharField(max_length=100, verbose_name="Mijoz ismi")
    purchase_date = models.DateField(verbose_name="Sotib olingan sana")
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon raqami")
    video = models.FileField(upload_to='reviews/videos/', blank=True, null=True, verbose_name="Mahsulot videosi")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Yuborilgan vaqt")

    class Meta:
        verbose_name = "Mijoz sharhi"
        verbose_name_plural = "Mijozlar sharhlari"
        ordering = ['-created_at']

    def clean(self):
        # Kamida 1 ta shart: Telefon raqami YOKI Video kiritilgan bo'lishi shart (har ikkisi ham bo'lishi mumkin)
        if not self.phone_number and not self.video:
            raise ValidationError("Kamida 1 ta shart bajarilishi shart: Telefon raqamingizni qoldiring YOKI mahsulot videosini yuklang!")

    def __str__(self):
        return f"{self.client_name} - {self.product.name}"
