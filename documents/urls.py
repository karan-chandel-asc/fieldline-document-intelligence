from django.urls import path

from . import views

urlpatterns = [
    path("inbox/", views.inbox, name="inbox"),
    path("review/", views.review, name="review"),
    path("exceptions/", views.exceptions, name="exceptions"),
]
