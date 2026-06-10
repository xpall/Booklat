from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class DemoReadOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEMO_MODE:
            return self.get_response(request)

        if not request.user.is_authenticated:
            return self.get_response(request)

        try:
            request.user.demo_profile
        except Exception:
            return self.get_response(request)

        path = request.path_info.lstrip("/")

        password_change_path = reverse("accounts:password_change").lstrip("/")
        if path == password_change_path:
            messages.error(request, "Demo accounts cannot change their password.")
            return redirect(request.META.get("HTTP_REFERER", "dashboard:index"))

        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            exempt_exact = {
                reverse("accounts:login").lstrip("/"),
                reverse("accounts:logout").lstrip("/"),
            }
            if path not in exempt_exact:
                messages.error(request, "Demo accounts have read-only access. Changes are not allowed.")
                referer = request.META.get("HTTP_REFERER", "")
                if referer:
                    return redirect(referer)
                return redirect("dashboard:index")

        return self.get_response(request)
