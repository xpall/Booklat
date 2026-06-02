import csv

from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, update_session_auth_hash
from django.contrib.auth import password_validation
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
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


def _get_success_redirect(user):
    if user.is_member:
        return redirect("books:book_list")
    return redirect("dashboard:index")


@require_http_methods(["GET", "POST"])
@ratelimit(key="ip", rate="5/m", method="POST")
def login_view(request):
    was_limited = getattr(request, "limited", False)
    if request.user.is_authenticated and request.user.status == User.Status.ACTIVE:
        return _get_success_redirect(request.user)
    if request.method == "POST":
        if was_limited:
            messages.error(request, "Too many login attempts. Please wait a minute and try again.")
            return render(request, "accounts/login.html", {"form": LoginForm()})
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
                return _get_success_redirect(user)
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
            update_session_auth_hash(request, request.user)
            log_action(request.user, "PASSWORD_CHANGED", "User", request.user.lrn)
            messages.success(request, "Password changed successfully.")
            if request.user.is_member:
                return redirect("books:book_list")
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
@ratelimit(key="user_or_ip", rate="10/m", method="POST")
def user_create_view(request):
    was_limited = getattr(request, "limited", False)
    if request.method == "POST":
        if was_limited:
            messages.error(request, "Too many requests. Please wait a minute and try again.")
            return redirect("accounts:user_list")
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
@ratelimit(key="user_or_ip", rate="5/m", method="POST")
def password_reset_view(request, user_id):
    was_limited = getattr(request, "limited", False)
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        if was_limited:
            messages.error(request, "Too many requests. Please wait a minute and try again.")
            return redirect("accounts:user_detail", user_id=user.pk)
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
@ratelimit(key="user_or_ip", rate="10/m", method="POST")
def user_import_view(request):
    was_limited = getattr(request, "limited", False)
    preview_data = None
    errors = []
    if request.method == "POST":
        if was_limited:
            messages.error(request, "Too many requests. Please wait a minute and try again.")
            return redirect("accounts:user_list")
        if "confirm" in request.POST:
            records = request.session.pop("import_records", None)
            if records:
                success, errors = _import_users(records, request.user)
                if success:
                    messages.success(request, f"Imported {success} users.")
                    return redirect("accounts:user_list")
                preview_data = _preview_users(records)
            form = CSVImportForm()
        else:
            form = CSVImportForm(request.POST, request.FILES)
            if form.is_valid():
                records = parse_csv_upload(request.FILES["csv_file"])
                if "preview" in request.POST:
                    preview_data = _preview_users(records)
                    request.session["import_records"] = records
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
    try:
        member_role = Role.objects.get(name="Member")
    except Role.DoesNotExist:
        member_role = None
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
            user = User(lrn=lrn, first_name=first_name, last_name=last_name, role=member_role, must_change_password=True)
            user.set_password(password)
            user.save()
            log_action(actor, "USER_CREATED", "User", user.lrn, metadata={"source": "csv_import"})
            imported += 1
        except Exception as e:
            errors.append(f"Row {i}: {lrn} - {str(e)}")
    return imported, errors


@permission_required("system.import_data")
def user_sample_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="users_sample.csv"'
    writer = csv.writer(response)
    writer.writerow(["first_name", "last_name", "lrn", "password"])
    writer.writerow(["Juan", "Dela Cruz", "LRN123456", "SecurePass1!"])
    return response