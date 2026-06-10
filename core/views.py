import csv
from datetime import datetime
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from core.decorators import permission_required
from core.models import AboutConfig
from accounts.models import User


def sw_js(request):
    path = settings.BASE_DIR / "core" / "static" / "core" / "sw.js"
    content = path.read_text()
    return HttpResponse(content, content_type="application/javascript")


def home_view(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if request.user.role and request.user.role.name == "Member":
        return redirect("dashboard:student_dashboard")
    return redirect("dashboard:index")


def about_view(request):
    config = AboutConfig.get_config()
    return render(request, "core/about.html", {
        "title": "About",
        "config": config,
    })


from books.models import Book, Category
from inventory.models import BookCopy
from loans.models import Loan
from audit.models import AuditLog


@permission_required("system.export_data")
def export_view(request):
    return render(request, "core/export.html")


@permission_required("system.export_data")
def export_users_csv(request):
    response = HttpResponse(content_type="text/csv")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    response["Content-Disposition"] = f'attachment; filename="booklat_users_{ts}.csv"'
    writer = csv.writer(response)
    writer.writerow(["first_name", "last_name", "lrn", "password"])
    for user in User.objects.iterator():
        writer.writerow([user.first_name, user.last_name, user.lrn, user.password])
    return response


@permission_required("system.export_data")
def export_categories_csv(request):
    response = HttpResponse(content_type="text/csv")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    response["Content-Disposition"] = f'attachment; filename="booklat_categories_{ts}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Slug", "Color", "Books", "Archived"])
    for cat in Category.objects.annotate(num_books=Count("book_set")).iterator():
        writer.writerow([cat.name, cat.slug, cat.color, cat.num_books, "Yes" if cat.is_archived else "No"])
    return response


@permission_required("system.export_data")
def export_books_csv(request):
    response = HttpResponse(content_type="text/csv")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    response["Content-Disposition"] = f'attachment; filename="booklat_books_{ts}.csv"'
    writer = csv.writer(response)
    writer.writerow(["isbn", "title", "subtitle", "authors", "publisher", "publication_year", "description", "categories", "cover_image"])
    for book in Book.objects.filter(is_archived=False).prefetch_related("categories").iterator(chunk_size=1000):
        cats = ", ".join(c.name for c in book.categories.all())
        writer.writerow([
            book.isbn, book.title, book.subtitle, book.authors,
            book.publisher, book.publication_year or "", book.description or "",
            cats, book.cover_image or "",
        ])
    return response


@permission_required("system.export_data")
def export_copies_csv(request):
    response = HttpResponse(content_type="text/csv")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    response["Content-Disposition"] = f'attachment; filename="booklat_copies_{ts}.csv"'
    writer = csv.writer(response)
    writer.writerow(["copy_id", "isbn", "acquisition_date", "donor", "status", "shelf_location", "notes"])
    for copy in BookCopy.objects.select_related("book").filter(is_archived=False).iterator():
        writer.writerow([
            copy.copy_id,
            copy.book.isbn,
            str(copy.acquisition_date) if copy.acquisition_date else "",
            copy.donor,
            copy.status,
            copy.shelf_location,
            copy.notes,
        ])
    return response


@permission_required("system.export_data")
def export_loans_csv(request):
    response = HttpResponse(content_type="text/csv")
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    response["Content-Disposition"] = f'attachment; filename="booklat_loans_{ts}.csv"'
    writer = csv.writer(response)
    writer.writerow(["User LRN", "First Name", "Last Name", "Copy ID", "Book Title", "Checkout Date", "Due Date", "Return Date"])
    for loan in Loan.objects.select_related("user", "book_copy__book").iterator():
        writer.writerow([
            loan.user.lrn,
            loan.user.first_name,
            loan.user.last_name,
            loan.book_copy.copy_id,
            loan.book_copy.book.title,
            str(loan.checkout_date),
            str(loan.due_date),
            str(loan.return_date) if loan.return_date else "",
        ])
    return response