import csv
from django.shortcuts import render, redirect
from django.http import HttpResponse
from core.decorators import permission_required
from accounts.models import User


def home_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if request.user.role and request.user.role.name == "Member":
        return redirect("books:book_list")
    return redirect("dashboard:index")


from books.models import Book
from inventory.models import BookCopy
from loans.models import Loan
from audit.models import AuditLog


@permission_required("system.export_data")
def export_view(request):
    return render(request, "core/export.html")


@permission_required("system.export_data")
def export_users_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="users.csv"'
    writer = csv.writer(response)
    writer.writerow(["LRN", "First Name", "Last Name", "Status", "Created At"])
    for user in User.objects.iterator():
        writer.writerow([user.lrn, user.first_name, user.last_name, user.status, user.created_at.strftime("%Y-%m-%d %H:%M:%S")])
    return response


@permission_required("system.export_data")
def export_books_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="books.csv"'
    writer = csv.writer(response)
    writer.writerow(["ISBN", "Title", "Publisher", "Publication Year", "Categories"])
    for book in Book.objects.filter(is_archived=False).iterator():
        writer.writerow([book.isbn, book.title, book.publisher, book.publication_year or "", book.categories])
    return response


@permission_required("system.export_data")
def export_copies_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="copies.csv"'
    writer = csv.writer(response)
    writer.writerow(["Copy ID", "Book ISBN", "Book Title", "Status", "Shelf Location", "Acquisition Date"])
    for copy in BookCopy.objects.select_related("book").filter(is_archived=False).iterator():
        writer.writerow([
            copy.copy_id,
            copy.book.isbn,
            copy.book.title,
            copy.get_status_display(),
            copy.shelf_location,
            str(copy.acquisition_date) if copy.acquisition_date else "",
        ])
    return response


@permission_required("system.export_data")
def export_loans_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="loans.csv"'
    writer = csv.writer(response)
    writer.writerow(["User LRN", "Copy ID", "Book Title", "Checkout Date", "Due Date", "Return Date"])
    for loan in Loan.objects.select_related("user", "book_copy__book").iterator():
        writer.writerow([
            loan.user.lrn,
            loan.book_copy.copy_id,
            loan.book_copy.book.title,
            str(loan.checkout_date),
            str(loan.due_date),
            str(loan.return_date) if loan.return_date else "",
        ])
    return response