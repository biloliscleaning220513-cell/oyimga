from django.contrib import admin
from django.utils.html import format_html

from .models import Bonus, Order, Product, ProductImage, Review, SiteSettings


def thumb(image, size=60):
    if image:
        return format_html('<img src="{}" style="height:{}px;border-radius:6px;object-fit:cover">', image.url, size)
    return "—"


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Bosh sahifa", {'fields': ('site_name', 'hero_image', 'hero_preview', 'hero_title', 'hero_subtitle')}),
        ("Aloqa (sayt pastida chiqadi)", {'fields': ('phone', 'instagram', 'telegram', 'telegram_bot', 'address')}),
    )
    readonly_fields = ('hero_preview',)

    @admin.display(description="Ko'rinishi")
    def hero_preview(self, obj):
        return thumb(obj.hero_image, 120)

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'position')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('preview', 'name', 'price', 'sizes', 'is_active', 'created_at')
    list_display_links = ('preview', 'name')
    list_editable = ('is_active',)
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'created_at')
    fields = ('name', 'price', 'image', 'sizes', 'description', 'is_active')
    inlines = [ProductImageInline]

    @admin.display(description="Rasm")
    def preview(self, obj):
        return thumb(obj.image)


@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    list_display = ('icon', 'title', 'position', 'is_active')
    list_display_links = ('title',)
    list_editable = ('position', 'is_active')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'phone', 'product', 'size', 'source', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'source', 'created_at')
    search_fields = ('customer_name', 'phone', 'product__name')
    readonly_fields = ('source', 'telegram_user_id', 'created_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'product', 'purchase_date', 'phone_number', 'has_video', 'created_at')
    list_filter = ('purchase_date', 'product', 'created_at')
    search_fields = ('client_name', 'phone_number', 'product__name')

    def has_video(self, obj):
        return bool(obj.video)
    has_video.boolean = True
    has_video.short_description = "Video bormi?"
