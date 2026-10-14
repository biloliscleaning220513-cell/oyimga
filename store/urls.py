from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/order/', views.product_order, name='product_order'),
    path('tg/<str:secret>/', views.telegram_webhook, name='telegram_webhook'),
]
