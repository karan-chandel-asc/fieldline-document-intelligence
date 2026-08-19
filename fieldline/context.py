from django.conf import settings


def brand(request):
    return {
        "FIVERR_GIG_URL": getattr(settings, "FIVERR_GIG_URL", "https://www.fiverr.com/"),
    }
