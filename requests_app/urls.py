from django.urls import path
from . import views

app_name = "requests_app"

urlpatterns = [
    path("", views.request_list_view, name="request_list"),
    path("book/<int:book_id>/", views.request_checkout_view, name="request_checkout"),
    path("<int:request_id>/cancel/", views.cancel_request_view, name="cancel_request"),
    path("<int:request_id>/process/", views.process_request_view, name="process_request"),
]