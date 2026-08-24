from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),
    path("", include("accounts.urls")),
    path("app/", include("dashboard.urls")),
    path("app/", include("documents.urls")),
    path("app/schemas/", include("schemas.urls")),
    path("app/exports/", include("exports.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
