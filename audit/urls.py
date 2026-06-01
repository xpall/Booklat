from django.urls import path
from . import views

app_name = "audit"

urlpatterns = [
    path("", views.audit_list_view, name="log_list"),
    path("<int:log_id>/", views.audit_detail_view, name="log_detail"),
    path("export/", views.audit_export_view, name="export"),
]