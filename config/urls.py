from django.urls import path, include

urlpatterns = [
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("books/", include("books.urls")),
    path("inventory/", include("inventory.urls")),
    path("loans/", include("loans.urls")),
    path("requests/", include("requests_app.urls")),
    path("audit/", include("audit.urls")),
    path("dashboard/", include("dashboard.urls")),
]