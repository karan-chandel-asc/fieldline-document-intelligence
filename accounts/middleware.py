from django.shortcuts import redirect
from django.urls import reverse
from urllib.parse import urlencode


class LoginRequiredMiddleware:
    """Send anonymous visitors on /app/ to sign-in, then back to the page they wanted."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/app/") and not request.user.is_authenticated:
            login_url = reverse("login")
            query = urlencode({"next": request.get_full_path()})
            return redirect(f"{login_url}?{query}")
        return self.get_response(request)
