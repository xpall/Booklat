from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.copy_list_view, name="copy_list"),
    path("create/", views.copy_create_view, name="copy_create"),
    path("import/", views.copy_import_view, name="copy_import"),
    path("<int:copy_id>/", views.copy_detail_view, name="copy_detail"),
    path("<int:copy_id>/edit/", views.copy_update_view, name="copy_edit"),
    path("<int:copy_id>/status/", views.copy_status_change_view, name="copy_status_change"),
    path("<int:copy_id>/archive/", views.copy_archive_view, name="copy_archive"),
]