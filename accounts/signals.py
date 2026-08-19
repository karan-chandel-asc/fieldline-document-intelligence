from django.contrib.auth.models import User

DEMO_EMAIL = "demo@fieldline.app"
DEMO_PASSWORD = "demo"


def create_demo_user(sender, **kwargs):
    if getattr(sender, "label", None) != "auth":
        return
    user, created = User.objects.get_or_create(
        username=DEMO_EMAIL,
        defaults={"email": DEMO_EMAIL},
    )
    if created:
        user.set_password(DEMO_PASSWORD)
        user.save()
