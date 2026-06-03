from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.copy_list_view, name="copy_list"),
    path("create/", views.copy_create_view, name="copy_create"),
    path("import/sample/", views.copy_sample_csv, name="copy_import_sample"),
    path("import/", views.copy_import_view, name="copy_import"),
    path("<str:copy_id>/", views.copy_detail_view, name="copy_detail"),
    path("<str:copy_id>/edit/", views.copy_update_view, name="copy_edit"),
    path("<str:copy_id>/status/", views.copy_status_change_view, name="copy_status_change"),
    path("<str:copy_id>/archive/", views.copy_archive_view, name="copy_archive"),
    path("<str:copy_id>/unarchive/", views.copy_unarchive_view, name="copy_unarchive"),
]