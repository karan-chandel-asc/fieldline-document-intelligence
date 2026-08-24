from django.urls import path

from . import views

urlpatterns = [
    path("inbox/api/upload/", views.DocumentUploadApiView.as_view(), name="documents_upload_api"),
    path("inbox/api/jobs/<int:job_id>/", views.ExtractionJobApiView.as_view(), name="extraction_job_api"),
    path("inbox/api/list/", views.DocumentListApiView.as_view(), name="documents_list_api"),
    path("inbox/", views.inbox, name="inbox"),
    path("review/", views.review, name="review"),
    path("exceptions/", views.exceptions, name="exceptions"),
]
