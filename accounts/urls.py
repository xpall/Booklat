from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("password-change/", views.password_change_view, name="password_change"),
    path("", views.user_list_view, name="user_list"),
    path("<int:user_id>/", views.user_detail_view, name="user_detail"),
    path("create/", views.user_create_view, name="user_create"),
    path("<int:user_id>/edit/", views.user_update_view, name="user_edit"),
    path("<int:user_id>/archive/", views.user_archive_view, name="user_archive"),
    path("<int:user_id>/suspend/", views.user_suspend_view, name="user_suspend"),
    path("<int:user_id>/activate/", views.user_activate_view, name="user_activate"),
    path("<int:user_id>/password-reset/", views.password_reset_view, name="password_reset"),
    path("import/", views.user_import_view, name="user_import"),
    path("import/sample/", views.user_sample_csv, name="user_import_sample"),
    path("search/", views.user_search_json, name="user_search_json"),
]