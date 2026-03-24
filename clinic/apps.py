import os

from django.apps import AppConfig
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate


class ClinicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'clinic'

    def ready(self):  # noqa: D401
        """Create default admin user if configured via environment variables."""

        def ensure_default_admin(sender, **kwargs):  # noqa: ANN001
            username = os.environ.get("DEFAULT_ADMIN_USERNAME", "admin").strip() or "admin"
            password = os.environ.get("DEFAULT_ADMIN_PASSWORD", "").strip()
            email = os.environ.get("DEFAULT_ADMIN_EMAIL", "admin@example.com").strip()

            # If password isn't provided, do nothing (safer than hardcoding a secret).
            if not password:
                if settings.DEBUG:
                    print(
                        "[ua-clinic] DEFAULT_ADMIN_PASSWORD not set; skipping default admin creation."
                    )
                return

            User = get_user_model()

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_staff": True,
                    "is_superuser": True,
                },
            )

            if created:
                user.set_password(password)
                user.is_staff = True
                user.is_superuser = True
                if hasattr(user, "email") and email:
                    user.email = email
                user.save()
                print(f"[ua-clinic] Created default admin user: {username}")
            else:
                # Ensure privileges are correct (but do NOT change password automatically)
                changed = False
                if not user.is_staff:
                    user.is_staff = True
                    changed = True
                if not user.is_superuser:
                    user.is_superuser = True
                    changed = True
                if hasattr(user, "email") and email and getattr(user, "email", "") != email:
                    user.email = email
                    changed = True
                if changed:
                    user.save()
                    print(f"[ua-clinic] Updated default admin privileges: {username}")

        post_migrate.connect(ensure_default_admin, sender=self)
