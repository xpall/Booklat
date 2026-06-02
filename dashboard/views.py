from django.shortcuts import render
from django.utils import timezone
from inventory.models import BookCopy
from books.models import Book
from loans.models import Loan
from requests_app.models import CheckoutRequest
from core.decorators import admin_or_staff_required


@admin_or_staff_required
def index(request):
    today = timezone.localdate()
    total_titles = Book.objects.filter(is_archived=False).count()
    borrowed_copies = BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.BORROWED).count()

    overdue_loans = Loan.objects.filter(return_date__isnull=True, due_date__lt=today).select_related("user", "book_copy__book")
    overdue_count = overdue_loans.count()

    pending_requests = CheckoutRequest.objects.filter(status=CheckoutRequest.Status.PENDING).select_related("user", "book")
    approved_today = CheckoutRequest.objects.filter(status=CheckoutRequest.Status.APPROVED, processed_at__date=today).count()
    rejected_today = CheckoutRequest.objects.filter(status=CheckoutRequest.Status.REJECTED, processed_at__date=today).count()

    recent_loans = Loan.objects.select_related("user", "book_copy__book").order_by("-created_at")[:10]
    recent_returns = Loan.objects.filter(return_date__isnull=False).select_related("user", "book_copy__book").order_by("-return_date")[:5]

    return render(request, "dashboard/index.html", {
        "total_titles": total_titles,
        "borrowed_copies": borrowed_copies,
        "overdue_count": overdue_count,
        "overdue_loans": overdue_loans,
        "pending_requests": pending_requests,
        "approved_today": approved_today,
        "rejected_today": rejected_today,
        "recent_loans": recent_loans,
        "recent_returns": recent_returns,
    })