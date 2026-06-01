from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth import password_validation
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import User, Role
from .forms import (
    LoginForm,
    PasswordChangeForm,
    PasswordResetForm,
    UserForm,
    UserUpdateForm,
    CSVImportForm,
)
from core.decorators import permission_required, any_permission_required, admin_or_staff_required
from core.utils import log_action, parse_csv_upload


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated and request.user.status == User.Status.ACTIVE:
        return redirect("dashboard:index")
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            from .backends import LRNAuthenticationBackend

            backend = LRNAuthenticationBackend()
            user = backend.authenticate(
                request,
                lrn=form.cleaned_data["lrn"],
                password=form.cleaned_data["password"],
            )
            if user:
                user.last_login = timezone.now()
                user.save(update_fields=["last_login"])
                auth_login(request, user)
                if user.must_change_password:
                    return redirect("accounts:password_change")
                return redirect("dashboard:index")
            messages.error(request, "Invalid LRN or password.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    auth_logout(request)
    return redirect("accounts:login")


@require_http_methods(["GET", "POST"])
def password_change_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data["new_password"])
            request.user.must_change_password = False
            request.user.save()
            log_action(request.user, "PASSWORD_CHANGED", "User", request.user.lrn)
            messages.success(request, "Password changed successfully.")
            return redirect("dashboard:index")
    else:
        form = PasswordChangeForm()
    return render(request, "accounts/password_change.html", {"form": form})


@permission_required("users.view")
def user_list_view(request):
    users = User.objects.exclude(status=User.Status.ARCHIVED).select_related("role")
    return render(request, "accounts/user_list.html", {"users": users})


@permission_required("users.view")
def user_detail_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return render(request, "accounts/user_detail.html", {"profile_user": user})


@require_http_methods(["GET", "POST"])
@permission_required("users.create")
def user_create_view(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.must_change_password = True
            user.save()
            log_action(request.user, "USER_CREATED", "User", user.lrn)
            messages.success(request, f"User {user.lrn} created.")
            return redirect("accounts:user_detail", user_id=user.pk)
    else:
        form = UserForm()
    return render(request, "accounts/user_form.html", {"form": form, "title": "Create User"})


@require_http_methods(["GET", "POST"])
@permission_required("users.update")
def user_update_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            log_action(request.user, "USER_UPDATED", "User", user.lrn)
            messages.success(request, f"User {user.lrn} updated.")
            return redirect("accounts:user_detail", user_id=user.pk)
    else:
        form = UserUpdateForm(instance=user)
    return render(request, "accounts/user_form.html", {"form": form, "title": f"Edit {user.get_full_name()}"})


@require_http_methods(["POST"])
@permission_required("users.archive")
def user_archive_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.status = User.Status.ARCHIVED
    user.save()
    log_action(request.user, "USER_ARCHIVED", "User", user.lrn)
    messages.success(request, f"User {user.lrn} archived.")
    return redirect("accounts:user_list")


@require_http_methods(["POST"])
@permission_required("users.update")
def user_suspend_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.status = User.Status.SUSPENDED
    user.save()
    log_action(request.user, "USER_SUSPENDED", "User", user.lrn)
    messages.success(request, f"User {user.lrn} suspended.")
    return redirect("accounts:user_detail", user_id=user.pk)


@require_http_methods(["POST"])
@permission_required("users.update")
def user_activate_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.status = User.Status.ACTIVE
    user.save()
    log_action(request.user, "USER_ACTIVATED", "User", user.lrn)
    messages.success(request, f"User {user.lrn} activated.")
    return redirect("accounts:user_detail", user_id=user.pk)


@require_http_methods(["GET", "POST"])
@permission_required("users.password_reset")
def password_reset_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data["new_password"])
            user.must_change_password = True
            user.save()
            log_action(request.user, "PASSWORD_RESET", "User", user.lrn)
            messages.success(request, f"Password reset for {user.lrn}.")
            return redirect("accounts:user_detail", user_id=user.pk)
    else:
        form = PasswordResetForm()
    return render(request, "accounts/password_reset.html", {"form": form, "profile_user": user})


@require_http_methods(["GET", "POST"])
@permission_required("system.import_data")
def user_import_view(request):
    preview_data = None
    errors = []
    if request.method == "POST":
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            records = parse_csv_upload(request.FILES["csv_file"])
            if "preview" in request.POST:
                preview_data = _preview_users(records)
            elif "confirm" in request.POST:
                success, errors = _import_users(records, request.user)
                if success:
                    messages.success(request, f"Imported {success} users.")
                    return redirect("accounts:user_list")
                preview_data = records
                preview_data = _preview_users(records)
    else:
        form = CSVImportForm()
    return render(request, "accounts/import.html", {
        "form": form,
        "preview_data": preview_data,
        "errors": errors,
        "title": "Import Users",
        "columns": ["First Name", "Last Name", "LRN"],
    })


def _preview_users(records):
    return [
        {
            "first_name": r.get("first_name", ""),
            "last_name": r.get("last_name", ""),
            "lrn": r.get("lrn", ""),
        }
        for r in records
    ]


def _import_users(records, actor):
    errors = []
    imported = 0
    for i, r in enumerate(records, 1):
        lrn = r.get("lrn", "").strip()
        first_name = r.get("first_name", "").strip()
        last_name = r.get("last_name", "").strip()
        password = r.get("password", "")
        if not lrn or not first_name or not last_name or not password:
            errors.append(f"Row {i}: missing required fields.")
            continue
        if User.objects.filter(lrn=lrn).exists():
            errors.append(f"Row {i}: LRN {lrn} already exists.")
            continue
        try:
            password_validation.validate_password(password)
        except Exception as e:
            errors.append(f"Row {i}: {lrn} - {e.messages[0]}")
            continue
        try:
            user = User(lrn=lrn, first_name=first_name, last_name=last_name, must_change_password=True)
            user.set_password(password)
            user.save()
            log_action(actor, "USER_CREATED", "User", user.lrn, metadata={"source": "csv_import"})
            imported += 1
        except Exception as e:
            errors.append(f"Row {i}: {lrn} - {str(e)}")
    return imported, errors