from django.urls import path

from . import views

urlpatterns = [
    path("api/ingest/", views.RecordIngestApiView.as_view(), name="records_ingest_api"),
    path("api/list/", views.RecordListApiView.as_view(), name="records_list_api"),
    path("", views.records, name="records"),
]
