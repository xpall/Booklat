from django.urls import path
from . import views

app_name = "announcements"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("create/", views.create_view, name="create"),
    path("<int:announcement_id>/update/", views.update_view, name="update"),
    path("<int:announcement_id>/archive/", views.archive_view, name="archive"),
]
