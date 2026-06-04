from django.urls import path
from . import views

app_name = "freedom_wall"

urlpatterns = [
    path("", views.post_list_view, name="post_list"),
    path("create/", views.post_create_view, name="post_create"),
    path("pending/", views.post_pending_view, name="post_pending"),
    path("<int:post_id>/process/", views.post_process_view, name="post_process"),
    path("<int:post_id>/delete/", views.post_delete_view, name="post_delete"),
    path("<int:post_id>/upvote/", views.post_upvote_view, name="post_upvote"),
]
