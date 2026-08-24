from django.urls import path

from . import views

urlpatterns = [
    path("inbox/api/upload/", views.DocumentUploadApiView.as_view(), name="documents_upload_api"),
    path("inbox/api/jobs/<int:job_id>/", views.ExtractionJobApiView.as_view(), name="extraction_job_api"),
    path("inbox/api/list/", views.DocumentListApiView.as_view(), name="documents_list_api"),
    path(
        "inbox/api/documents/<int:document_id>/retry/",
        views.DocumentRetryApiView.as_view(),
        name="document_retry_api",
    ),
    path(
        "inbox/api/documents/<int:document_id>/",
        views.DocumentDetailApiView.as_view(),
        name="document_detail_api",
    ),
    path("inbox/", views.inbox, name="inbox"),
    path("review/", views.review, name="review"),
    path("exceptions/", views.exceptions, name="exceptions"),
]
