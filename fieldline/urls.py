from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import FileResponse
from django.urls import include, path


def favicon(request):
    return FileResponse(
        (settings.BASE_DIR / "static" / "favicon.svg").open("rb"),
        content_type="image/svg+xml",
    )


urlpatterns = [
    path("favicon.ico", favicon, name="favicon"),
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),
    path("", include("accounts.urls")),
    path("app/", include("dashboard.urls")),
    path("app/", include("documents.urls")),
    path("app/schemas/", include("schemas.urls")),
    path("app/exports/", include("exports.urls")),
    path("app/records/", include("records.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
