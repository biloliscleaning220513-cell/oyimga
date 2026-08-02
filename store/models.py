from django.db import models
from django.core.exceptions import ValidationError

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Mahsulot nomi")
    description = models.TextField(verbose_name="Tavsif")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Narxi (so'm)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan sana")

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

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
