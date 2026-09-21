import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = "Ensure initial admin user exists"

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_ADMIN_USERNAME")
        email = os.getenv("DJANGO_ADMIN_EMAIL")
        password = os.getenv("DJANGO_ADMIN_PASSWORD")

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f"Superuser '{username}' already exists.")
            )
            return

        with transaction.atomic():
            # 1. Create the core authentication record
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    f"Superuser '{user.username}' and associated profile"
                    "created successfully."
                )
            )
        )
