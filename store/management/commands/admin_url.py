from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Maxfiy admin panel manzilini ko'rsatadi"

    def handle(self, *args, **options):
        base = settings.SITE_URL or 'http://127.0.0.1:8000'
        self.stdout.write(f"Admin panel: {base}/{settings.ADMIN_URL}")
