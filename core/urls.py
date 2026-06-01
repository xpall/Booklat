from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = "core"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="dashboard:index")),
    path("export/", views.export_view, name="export"),
    path("export/users/", views.export_users_csv, name="export_users_csv"),
    path("export/books/", views.export_books_csv, name="export_books_csv"),
    path("export/copies/", views.export_copies_csv, name="export_copies_csv"),
    path("export/loans/", views.export_loans_csv, name="export_loans_csv"),
]