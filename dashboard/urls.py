from django.urls import path

from . import views

urlpatterns = [
    path("api/overview/", views.DashboardOverviewApiView.as_view(), name="dashboard_overview_api"),
    path("", views.dashboard, name="dashboard"),
]
