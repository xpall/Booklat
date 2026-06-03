from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    path("", views.book_list_view, name="book_list"),
    path("create/", views.book_create_view, name="book_create"),
    path("import/sample/", views.book_sample_csv, name="book_import_sample"),
    path("import/", views.book_import_view, name="book_import"),
    path("search/", views.book_search_json, name="book_search_json"),
    path("<str:isbn>/", views.book_detail_view, name="book_detail"),
    path("<str:isbn>/add-copy/", views.book_add_copy_view, name="book_add_copy"),
    path("<str:isbn>/edit/", views.book_update_view, name="book_edit"),
    path("<str:isbn>/archive/", views.book_archive_view, name="book_archive"),
    path("<str:isbn>/unarchive/", views.book_unarchive_view, name="book_unarchive"),
]