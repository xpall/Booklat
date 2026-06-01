from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from core.decorators import admin_or_staff_required
from inventory.models import BookCopy
from books.models import Book
from accounts.models import User
from loans.models import Loan
from requests_app.models import CheckoutRequest


@admin_or_staff_required
def index(request):
    today = timezone.localdate()
    total_titles = Book.objects.filter(is_archived=False).count()
    total_copies = BookCopy.objects.filter(is_archived=False).count()
    available_copies = BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.AVAILABLE).count()
    borrowed_copies = BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.BORROWED).count()
    reserved_copies = BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.RESERVED).count()
    lost_copies = BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.LOST).count()
    damaged_copies = BookCopy.objects.filter(is_archived=False, status=BookCopy.Status.DAMAGED).count()
    total_members = User.objects.filter(status=User.Status.ACTIVE).count()

    overdue_loans = Loan.objects.filter(return_date__isnull=True, due_date__lt=today).select_related("user", "book_copy__book")

    pending_requests = CheckoutRequest.objects.filter(status=CheckoutRequest.Status.PENDING).select_related("user", "book")
    approved_today = CheckoutRequest.objects.filter(status=CheckoutRequest.Status.APPROVED, processed_at__date=today).count()
    rejected_today = CheckoutRequest.objects.filter(status=CheckoutRequest.Status.REJECTED, processed_at__date=today).count()

    recent_loans = Loan.objects.select_related("user", "book_copy__book").order_by("-created_at")[:10]
    recent_returns = Loan.objects.filter(return_date__isnull=False).select_related("user", "book_copy__book").order_by("-return_date")[:5]
    new_users = User.objects.order_by("-created_at")[:5]

    return render(request, "dashboard/index.html", {
        "total_titles": total_titles,
        "total_copies": total_copies,
        "available_copies": available_copies,
        "borrowed_copies": borrowed_copies,
        "reserved_copies": reserved_copies,
        "lost_copies": lost_copies,
        "damaged_copies": damaged_copies,
        "total_members": total_members,
        "overdue_loans": overdue_loans,
        "pending_requests": pending_requests,
        "approved_today": approved_today,
        "rejected_today": rejected_today,
        "recent_loans": recent_loans,
        "recent_returns": recent_returns,
        "new_users": new_users,
    })