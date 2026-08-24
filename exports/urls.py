from django.urls import path

from . import views

urlpatterns = [
    path("api/create/", views.ExportCreateApiView.as_view(), name="export_create_api"),
    path("api/list/", views.ExportListApiView.as_view(), name="export_list_api"),
    path("api/sql/", views.ExportSqlApiView.as_view(), name="export_sql_api"),
    path("api/webhooks/test/", views.WebhookTestApiView.as_view(), name="webhook_test_api"),
    path("api/webhooks/", views.WebhookApiView.as_view(), name="webhook_api"),
    path("api/<int:export_id>/download/", views.ExportDownloadApiView.as_view(), name="export_download_api"),
    path("", views.exports, name="exports"),
]
