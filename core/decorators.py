from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def permission_required(perm_codename):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")
            roles = request.user.roles.all()
            if not roles:
                raise PermissionDenied
            from accounts.models import RolePermission

            has_perm = RolePermission.objects.filter(
                role__in=roles, permission__codename=perm_codename
            ).exists()
            if not has_perm:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def any_permission_required(*perm_codenames):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("accounts:login")
            roles = request.user.roles.all()
            if not roles:
                raise PermissionDenied
            from accounts.models import RolePermission

            for codename in perm_codenames:
                if RolePermission.objects.filter(
                    role__in=roles, permission__codename=codename
                ).exists():
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied

        return wrapper

    return decorator


def admin_or_staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if request.user.role.name not in ("Administrator", "Staff"):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapper