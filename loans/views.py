from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from django_ratelimit.decorators import ratelimit
from .models import Loan
from accounts.models import User
from inventory.models import BookCopy, CopyHistory
from .forms import CheckoutUserForm, CheckoutCopyForm, ReturnUserForm, ReturnCopyForm
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
@ratelimit(key="user_or_ip", rate="10/m", method="POST")
def checkout_view(request):
    was_limited = getattr(request, "limited", False)
    if request.method == "POST":
        if was_limited:
            messages.error(request, "Too many requests. Please wait a minute and try again.")
            return redirect("loans:loan_list")
        if "user" in request.POST:
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
    return render(request, "loans/checkout_copy.html", {"form": form, "checkout_user": user})


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
        due_str = request.POST.get("due_date", "")
        due_date = timezone.datetime.strptime(due_str, "%Y-%m-%d").date() if due_str else today + timedelta(days=7)
        loan = Loan(
            user=user,
            book_copy=copy,
            checkout_date=today,
            due_date=due_date,
            processed_by=request.user,
        )
        loan.save()
        copy.status = BookCopy.Status.BORROWED
        copy.save()
        CopyHistory.objects.create(book_copy=copy, event="Borrowed", notes=f"Checked out by {user.lrn}", actor=request.user)
        log_action(request.user, "LOAN_CREATED", "Loan", loan.loan_id, metadata={
            "user_lrn": user.lrn,
            "copy_id": copy.copy_id,
            "due_date": str(loan.due_date),
        })
        request.session.pop("checkout_user_id", None)
        request.session.pop("checkout_copy_id", None)
        messages.success(request, f"Book checked out to {user.get_full_name()}.")
        return redirect("loans:loan_list")
    return render(request, "loans/checkout_confirm.html", {
        "checkout_user": user, "copy": copy,
        "default_due_date": timezone.localdate() + timedelta(days=7),
    })


@require_http_methods(["GET", "POST"])
@permission_required("loans.return")
@ratelimit(key="user_or_ip", rate="10/m", method="POST")
def return_book_view(request):
    was_limited = getattr(request, "limited", False)
    if request.method == "POST":
        if was_limited:
            messages.error(request, "Too many requests. Please wait a minute and try again.")
            return redirect("loans:loan_list")
        form = ReturnUserForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data["user"]
            request.session["return_user_id"] = user.pk
            return redirect("loans:return_select_copy")
    else:
        form = ReturnUserForm()
    return render(request, "loans/return_user.html", {"form": form})


@require_http_methods(["GET", "POST"])
@permission_required("loans.return")
def return_select_copy(request):
    user_id = request.session.get("return_user_id")
    if not user_id:
        return redirect("loans:return_book")
    return_user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = ReturnCopyForm(request.POST)
        if form.is_valid():
            copy = form.cleaned_data["copy"]
            loan = Loan.objects.filter(book_copy=copy, return_date__isnull=True).first()
            if not loan:
                messages.error(request, "No active loan found for this copy.")
                return redirect("loans:return_select_copy")
            if loan.user.pk != return_user.pk:
                messages.error(request, "This copy is not borrowed by the selected user.")
                return redirect("loans:return_select_copy")
            request.session["return_copy_id"] = copy.pk
            return redirect("loans:return_confirm")
    else:
        form = ReturnCopyForm()
    return render(request, "loans/return_copy.html", {
        "form": form,
        "return_user": return_user,
    })


@require_http_methods(["GET", "POST"])
@permission_required("loans.return")
def return_confirm(request):
    user_id = request.session.get("return_user_id")
    copy_id = request.session.get("return_copy_id")
    if not user_id or not copy_id:
        return redirect("loans:return_book")
    return_user = get_object_or_404(User, pk=user_id)
    copy = get_object_or_404(BookCopy, pk=copy_id)
    loan = Loan.objects.filter(book_copy=copy, return_date__isnull=True).first()
    if not loan:
        messages.error(request, "No active loan found for this copy.")
        return redirect("loans:loan_list")
    if request.method == "POST":
        loan.return_date = timezone.localdate()
        loan.save()
        copy.status = BookCopy.Status.AVAILABLE
        copy.save()
        CopyHistory.objects.create(book_copy=copy, event="Returned", actor=request.user)
        log_action(request.user, "LOAN_RETURNED", "Loan", loan.loan_id, metadata={
            "user_lrn": loan.user.lrn,
            "copy_id": copy.copy_id,
        })
        request.session.pop("return_user_id", None)
        request.session.pop("return_copy_id", None)
        messages.success(request, f"Book returned: {copy.copy_id}.")
        return redirect("loans:loan_list")
    return render(request, "loans/return_confirm.html", {
        "return_user": return_user,
        "copy": copy,
        "loan": loan,
    })


@any_permission_required("loans.return", "loans.create")
def borrowed_copy_search_json(request):
    q = request.GET.get("q", "").strip()
    user_id = request.GET.get("user_id")
    copies = BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.BORROWED).select_related("book")
    if user_id:
        active_loan_copy_ids = Loan.objects.filter(
            user_id=user_id, return_date__isnull=True
        ).values_list("book_copy_id", flat=True)
        copies = copies.filter(pk__in=active_loan_copy_ids)
    if q:
        copies = copies.filter(
            copy_id__icontains=q
        ) | copies.filter(
            book__title__icontains=q
        )
    copies = copies.distinct()[:20]
    results = [{"id": c.pk, "copy_id": c.copy_id, "title": c.book.title} for c in copies]
    return JsonResponse({"results": results})


@admin_or_staff_required
def overdue_list_view(request):
    overdue = Loan.objects.filter(
        return_date__isnull=True, due_date__lt=timezone.localdate()
    ).select_related("user", "book_copy__book")
    return render(request, "loans/overdue_list.html", {"loans": overdue})


@any_permission_required("loans.view")
def user_loans_view(request, lrn):
    user = get_object_or_404(User, lrn=lrn)
    if request.user.is_member and request.user.lrn != lrn:
        messages.error(request, "You can only view your own loans.")
        return redirect("books:book_list")
    loans = Loan.objects.filter(user=user).select_related("book_copy__book")
    return render(request, "loans/user_loans.html", {"profile_user": user, "loans": loans})