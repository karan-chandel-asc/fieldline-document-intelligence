from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme


class HelperServices:
    @staticmethod
    def schema_error(exc):
        return exc.errors()[0]["msg"].replace("Value error, ", "")

    @staticmethod
    def form_data(request):
        return request.POST.dict() if hasattr(request.POST, "dict") else dict(request.POST)

    @staticmethod
    def request_data(request):
        data = getattr(request, "data", None)
        if data is None:
            return HelperServices.form_data(request)
        if isinstance(data, dict) and not hasattr(data, "getlist"):
            return dict(data)
        if hasattr(data, "dict"):
            return data.dict()
        return dict(data)

    @staticmethod
    def safe_next(request, raw=None):
        if raw is None:
            raw = ""
            data = getattr(request, "data", None)
            if data is not None:
                try:
                    raw = data.get("next") or ""
                except Exception:
                    raw = ""
            raw = raw or request.POST.get("next") or request.GET.get("next") or ""
        if raw and url_has_allowed_host_and_scheme(
            raw,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return raw
        return reverse("dashboard")
