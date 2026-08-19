from django.urls import include, path
from django.contrib import admin

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("pages.urls")),
    path("", include("accounts.urls")),
    path("app/", include("dashboard.urls")),
    path("app/", include("documents.urls")),
    path("app/schemas/", include("schemas.urls")),
    path("app/exports/", include("exports.urls")),
]
