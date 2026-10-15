from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

admin.site.site_header = "Boshqaruv paneli"
admin.site.site_title = "Boshqaruv"
admin.site.index_title = "Do'kon boshqaruvi"

urlpatterns = [
    # Admin panel faqat maxfiy manzilda ochiladi, /admin/ esa 404 qaytaradi
    path(settings.ADMIN_URL, admin.site.urls),
    path('', include('store.urls')),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
