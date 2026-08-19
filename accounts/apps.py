from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    name = "accounts"
    verbose_name = "Accounts"

    def ready(self):
        from .signals import create_demo_user

        post_migrate.connect(create_demo_user, dispatch_uid="accounts.create_demo_user")
