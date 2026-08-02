from django.contrib import admin
from .models import Product, Review

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'product', 'purchase_date', 'phone_number', 'has_video', 'created_at')
    list_filter = ('purchase_date', 'product', 'created_at')
    search_fields = ('client_name', 'phone_number', 'product__name')

    def has_video(self, obj):
        return bool(obj.video)
    has_video.boolean = True
    has_video.short_description = "Video bormi?"
