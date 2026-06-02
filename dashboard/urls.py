from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.index, name="index"),
    path("student/", views.student_dashboard, name="student_dashboard"),
]