from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from .models import CheckoutRequest
from inventory.models import BookCopy, CopyHistory
from loans.models import Loan
from .forms import RequestCheckoutForm, ProcessRequestForm
from core.decorators import permission_required, any_permission_required, admin_or_staff_required
from core.utils import log_action


@any_permission_required("requests.view")
def request_list_view(request):
    if request.user.is_member:
        requests = CheckoutRequest.objects.filter(user=request.user)
    else:
        requests = CheckoutRequest.objects.select_related("user", "book")
    status_filter = request.GET.get("status", "")
    if status_filter:
        requests = requests.filter(status=status_filter)
    return render(request, "requests_app/request_list.html", {
        "requests": requests,
        "status_filter": status_filter,
        "status_choices": CheckoutRequest.Status.choices,
    })


@require_http_methods(["POST"])
def request_checkout_view(request, book_id):
    from books.models import Book
    book = get_object_or_404(Book, pk=book_id, is_archived=False)
    existing = CheckoutRequest.objects.filter(
        user=request.user,
        book=book,
        status=CheckoutRequest.Status.PENDING,
    ).first()
    if existing:
        messages.warning(request, "You already have a pending request for this book.")
        return redirect("books:book_detail", book_id=book.pk)
    req = CheckoutRequest(user=request.user, book=book)
    req.save()
    log_action(request.user, "CHECKOUT_REQUEST_CREATED", "CheckoutRequest", str(req.pk), metadata={
        "user_lrn": request.user.lrn,
        "book_isbn": book.isbn,
    })
    messages.success(request, f"Checkout requested for '{book.title}'.")
    return redirect("books:book_detail", book_id=book.pk)


@require_http_methods(["POST"])
def cancel_request_view(request, request_id):
    req = get_object_or_404(CheckoutRequest, pk=request_id, user=request.user)
    if req.status != CheckoutRequest.Status.PENDING:
        messages.error(request, "Only pending requests can be cancelled.")
        return redirect("requests_app:request_list")
    req.status = CheckoutRequest.Status.CANCELLED
    req.save()
    log_action(request.user, "CHECKOUT_REQUEST_CANCELLED", "CheckoutRequest", str(req.pk))
    messages.success(request, "Request cancelled.")
    return redirect("requests_app:request_list")


@require_http_methods(["GET", "POST"])
@permission_required("requests.process")
def process_request_view(request, request_id):
    req = get_object_or_404(CheckoutRequest.objects.select_related("user", "book"), pk=request_id)
    available_copies = req.book.copies.filter(is_archived=False, status=BookCopy.Status.AVAILABLE)
    if request.method == "POST":
        form = ProcessRequestForm(request.POST, available_copies=available_copies)
        if form.is_valid():
            action = form.cleaned_data["action"]
            if action == "approve":
                copy = form.cleaned_data["copy"]
                if copy:
                    today = timezone.localdate()
                    loan = Loan(
                        user=req.user,
                        book_copy=copy,
                        checkout_date=today,
                        due_date=today + timedelta(days=7),
                        processed_by=request.user,
                    )
                    loan.save()
                    copy.status = BookCopy.Status.BORROWED
                    copy.save()
                    CopyHistory.objects.create(book_copy=copy, event="Borrowed", notes=f"Approved request by {req.user.lrn}")
                    req.status = CheckoutRequest.Status.FULFILLED
                    req.notes = form.cleaned_data.get("notes", "")
                    req.processed_by = request.user
                    req.processed_at = timezone.now()
                    req.save()
                    log_action(request.user, "CHECKOUT_REQUEST_APPROVED", "CheckoutRequest", str(req.pk), metadata={
                        "user_lrn": req.user.lrn,
                        "copy_id": copy.copy_id,
                    })
                    messages.success(request, "Request approved and loan created.")
                    return redirect("requests_app:request_list")
            elif action == "reject":
                req.status = CheckoutRequest.Status.REJECTED
                req.notes = form.cleaned_data.get("notes", "")
                req.processed_by = request.user
                req.processed_at = timezone.now()
                req.save()
                log_action(request.user, "CHECKOUT_REQUEST_REJECTED", "CheckoutRequest", str(req.pk), metadata={
                    "user_lrn": req.user.lrn,
                    "notes": req.notes,
                })
                messages.success(request, "Request rejected.")
                return redirect("requests_app:request_list")
    else:
        form = ProcessRequestForm(available_copies=available_copies)
    return render(request, "requests_app/process.html", {
        "form": form,
        "request_obj": req,
        "available_copies": available_copies,
    })