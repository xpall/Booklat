from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from .models import Loan
from accounts.models import User
from inventory.models import BookCopy, CopyHistory
from .forms import CheckoutUserForm, CheckoutCopyForm, ReturnForm
from core.decorators import permission_required, any_permission_required, admin_or_staff_required
from core.utils import log_action


@admin_or_staff_required
def loan_list_view(request):
    query = request.GET.get("q", "")
    loans = Loan.objects.select_related("user", "book_copy__book")
    if query:
        loans = loans.filter(
            user__lrn__icontains=query
        ) | loans.filter(
            book_copy__copy_id__icontains=query
        ) | loans.filter(
            book_copy__book__title__icontains=query
        )
    return render(request, "loans/loan_list.html", {"loans": loans.distinct(), "query": query})


@require_http_methods(["GET", "POST"])
@permission_required("loans.create")
def checkout_view(request):
    if request.method == "POST":
        if "user_id" in request.POST:
            form = CheckoutUserForm(request.POST)
            if form.is_valid():
                user = form.cleaned_data["user"]
                request.session["checkout_user_id"] = user.pk
                return redirect("loans:checkout_select_copy")
        elif "copy_id" in request.POST:
            form = CheckoutCopyForm(request.POST)
            if form.is_valid():
                copy = form.cleaned_data["copy"]
                request.session["checkout_copy_id"] = copy.pk
                return redirect("loans:checkout_confirm")
    else:
        form = CheckoutUserForm()
    return render(request, "loans/checkout_user.html", {"form": form})


@require_http_methods(["GET", "POST"])
@permission_required("loans.create")
def checkout_select_copy(request):
    user_id = request.session.get("checkout_user_id")
    if not user_id:
        return redirect("loans:checkout")
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = CheckoutCopyForm(request.POST)
        if form.is_valid():
            copy = form.cleaned_data["copy"]
            request.session["checkout_copy_id"] = copy.pk
            return redirect("loans:checkout_confirm")
    else:
        form = CheckoutCopyForm()
    return render(request, "loans/checkout_copy.html", {"form": form, "user": user})


@require_http_methods(["GET", "POST"])
@permission_required("loans.create")
def checkout_confirm(request):
    user_id = request.session.get("checkout_user_id")
    copy_id = request.session.get("checkout_copy_id")
    if not user_id or not copy_id:
        return redirect("loans:checkout")
    user = get_object_or_404(User, pk=user_id)
    copy = get_object_or_404(BookCopy, pk=copy_id)
    if request.method == "POST":
        if copy.status != BookCopy.Status.AVAILABLE:
            messages.error(request, "Copy is not available.")
            return redirect("loans:checkout")
        today = timezone.localdate()
        loan = Loan(
            user=user,
            book_copy=copy,
            checkout_date=today,
            due_date=today + timedelta(days=7),
            processed_by=request.user,
        )
        loan.save()
        copy.status = BookCopy.Status.BORROWED
        copy.save()
        CopyHistory.objects.create(book_copy=copy, event="Borrowed", notes=f"Checked out by {user.lrn}")
        log_action(request.user, "LOAN_CREATED", "Loan", str(loan.pk), metadata={
            "user_lrn": user.lrn,
            "copy_id": copy.copy_id,
            "due_date": str(loan.due_date),
        })
        request.session.pop("checkout_user_id", None)
        request.session.pop("checkout_copy_id", None)
        messages.success(request, f"Book checked out to {user.get_full_name()}.")
        return redirect("loans:loan_list")
    return render(request, "loans/checkout_confirm.html", {"user": user, "copy": copy})


@require_http_methods(["GET", "POST"])
@permission_required("loans.return")
def return_book_view(request):
    if request.method == "POST":
        form = ReturnForm(request.POST)
        if form.is_valid():
            copy = form.cleaned_data["copy"]
            loan = Loan.objects.filter(book_copy=copy, return_date__isnull=True).first()
            if not loan:
                messages.error(request, "No active loan found for this copy.")
                return redirect("loans:return_book")
            loan.return_date = timezone.localdate()
            loan.save()
            copy.status = BookCopy.Status.AVAILABLE
            copy.save()
            CopyHistory.objects.create(book_copy=copy, event="Returned")
            log_action(request.user, "LOAN_RETURNED", "Loan", str(loan.pk), metadata={
                "user_lrn": loan.user.lrn,
                "copy_id": copy.copy_id,
            })
            messages.success(request, f"Book returned: {copy.copy_id}.")
            return redirect("loans:loan_list")
    else:
        form = ReturnForm()
    return render(request, "loans/return_form.html", {"form": form})


@admin_or_staff_required
def overdue_list_view(request):
    overdue = Loan.objects.filter(
        return_date__isnull=True, due_date__lt=timezone.localdate()
    ).select_related("user", "book_copy__book")
    return render(request, "loans/overdue_list.html", {"loans": overdue})


@any_permission_required("loans.view")
def user_loans_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.user.is_member and request.user.pk != user.pk:
        messages.error(request, "You can only view your own loans.")
        return redirect("dashboard:index")
    loans = Loan.objects.filter(user=user).select_related("book_copy__book")
    return render(request, "loans/user_loans.html", {"profile_user": user, "loans": loans})