from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    path("", views.book_list_view, name="book_list"),
    path("create/", views.book_create_view, name="book_create"),
    path("import/sample/", views.book_sample_csv, name="book_import_sample"),
    path("import/", views.book_import_view, name="book_import"),
    path("<int:book_id>/", views.book_detail_view, name="book_detail"),
    path("<int:book_id>/edit/", views.book_update_view, name="book_edit"),
    path("<int:book_id>/archive/", views.book_archive_view, name="book_archive"),
]