from django.urls import path
from . import views

app_name = "books"

urlpatterns = [
    path("", views.book_list_view, name="book_list"),
    path("create/", views.book_create_view, name="book_create"),
    path("import/sample/", views.book_sample_csv, name="book_import_sample"),
    path("import/", views.book_import_view, name="book_import"),
    path("search/", views.book_search_json, name="book_search_json"),
    path("categories/", views.category_list_view, name="category_list"),
    path("categories/create/", views.category_create_view, name="category_create"),
    path("categories/export/", views.category_export_csv, name="category_export"),
    path("categories/import/", views.category_import_view, name="category_import"),
    path("categories/import/sample/", views.category_sample_csv, name="category_import_sample"),
    path("categories/<slug:slug>/edit/", views.category_update_view, name="category_edit"),
    path("categories/<slug:slug>/archive/", views.category_archive_view, name="category_archive"),
    path("categories/<slug:slug>/unarchive/", views.category_unarchive_view, name="category_unarchive"),
    path("<str:isbn>/", views.book_detail_view, name="book_detail"),
    path("<str:isbn>/add-copy/", views.book_add_copy_view, name="book_add_copy"),
    path("<str:isbn>/edit/", views.book_update_view, name="book_edit"),
    path("<str:isbn>/archive/", views.book_archive_view, name="book_archive"),
    path("<str:isbn>/unarchive/", views.book_unarchive_view, name="book_unarchive"),
]