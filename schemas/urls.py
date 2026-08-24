from django.urls import path

from . import views

urlpatterns = [
    path("", views.schemas, name="schemas"),
    path("api/save/", views.SchemaSaveApiView.as_view(), name="schema_save_api"),
    path("api/list/", views.SchemaListApiView.as_view(), name="schema_list_api"),
    path("api/<int:schema_id>/", views.SchemaDeleteApiView.as_view(), name="schema_delete_api"),
]
