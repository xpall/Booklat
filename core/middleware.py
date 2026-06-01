from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info.lstrip("/")
            exempt = [
                reverse("accounts:login").lstrip("/"),
                reverse("accounts:password_change").lstrip("/"),
                "static/",
            ]
            if not any(path.startswith(e) for e in exempt):
                return redirect("accounts:login")
        return self.get_response(request)


class MustChangePasswordMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.must_change_password:
            path = request.path_info.lstrip("/")
            exempt = [
                reverse("accounts:login").lstrip("/"),
                reverse("accounts:password_change").lstrip("/"),
                reverse("accounts:logout").lstrip("/"),
            ]
            if not any(path.startswith(e) for e in exempt):
                return redirect("accounts:password_change")
        return self.get_response(request)