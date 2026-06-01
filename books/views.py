import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Book
from .forms import BookForm, BookImportForm
from core.decorators import permission_required, any_permission_required
from core.utils import log_action, parse_csv_upload


@any_permission_required("books.view")
def book_list_view(request):
    query = request.GET.get("q", "")
    books = Book.objects.filter(is_archived=False)
    if query:
        books = books.filter(title__icontains=query) | books.filter(authors__icontains=query) | books.filter(isbn__icontains=query)
    books = books.distinct()
    return render(request, "books/book_list.html", {"books": books, "query": query})


@any_permission_required("books.view")
def book_detail_view(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    copies = book.copies.filter(is_archived=False)
    return render(request, "books/book_detail.html", {"book": book, "copies": copies})


@require_http_methods(["GET", "POST"])
@permission_required("books.create")
def book_create_view(request):
    if request.method == "POST":
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            log_action(request.user, "BOOK_CREATED", "Book", book.isbn)
            messages.success(request, f"Book '{book.title}' created.")
            return redirect("books:book_detail", book_id=book.pk)
    else:
        form = BookForm()
    return render(request, "books/book_form.html", {"form": form, "title": "Create Book"})


@require_http_methods(["GET", "POST"])
@permission_required("books.update")
def book_update_view(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if request.method == "POST":
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            log_action(request.user, "BOOK_UPDATED", "Book", book.isbn)
            messages.success(request, f"Book '{book.title}' updated.")
            return redirect("books:book_detail", book_id=book.pk)
    else:
        form = BookForm(instance=book)
    return render(request, "books/book_form.html", {"form": form, "title": f"Edit {book.title}"})


@require_http_methods(["POST"])
@permission_required("books.archive")
def book_archive_view(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    book.is_archived = True
    book.save()
    log_action(request.user, "BOOK_ARCHIVED", "Book", book.isbn)
    messages.success(request, f"Book '{book.title}' archived.")
    return redirect("books:book_list")


@require_http_methods(["GET", "POST"])
@permission_required("system.import_data")
def book_import_view(request):
    preview_data = None
    errors = []
    form = None
    if request.method == "POST":
        if "confirm" in request.POST:
            records = request.session.pop("import_preview_data", None)
            if records:
                imported, errors = _import_books(records, request.user)
                if imported:
                    messages.success(request, f"Imported {imported} books.")
                    return redirect("books:book_list")
                preview_data = records
            else:
                messages.error(request, "Import session expired. Please upload the file again.")
                form = BookImportForm()
        else:
            form = BookImportForm(request.POST, request.FILES)
            if form.is_valid():
                records = parse_csv_upload(request.FILES["csv_file"])
                preview_data = records
                request.session["import_preview_data"] = records
    else:
        form = BookImportForm()
        request.session.pop("import_preview_data", None)
    return render(request, "books/import.html", {
        "form": form if not preview_data else None,
        "preview_data": preview_data,
        "errors": errors,
        "title": "Import Books",
        "columns": ["ISBN", "Title", "Authors", "Publisher", "Publication Year", "Categories"],
    })


def _import_books(records, actor):
    errors = []
    imported = 0
    for i, r in enumerate(records, 1):
        isbn = r.get("isbn", "").strip()
        title = r.get("title", "").strip()
        if not isbn or not title:
            errors.append(f"Row {i}: missing ISBN or title.")
            continue
        if Book.objects.filter(isbn=isbn).exists():
            errors.append(f"Row {i}: ISBN {isbn} already exists.")
            continue
        try:
            book = Book(
                isbn=isbn,
                title=title,
                subtitle=r.get("subtitle", "").strip(),
                authors=r.get("authors", "").strip(),
                publisher=r.get("publisher", "").strip(),
                publication_year=r.get("publication_year") or None,
                description=r.get("description", "").strip(),
                categories=r.get("categories", "").strip(),
                cover_image=r.get("cover_image", "").strip(),
            )
            book.save()
            log_action(actor, "BOOK_CREATED", "Book", book.isbn, metadata={"source": "csv_import"})
            imported += 1
        except Exception as e:
            errors.append(f"Row {i}: {isbn} - {str(e)}")
    return imported, errors


@permission_required("system.import_data")
def book_sample_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="books_sample.csv"'
    writer = csv.writer(response)
    writer.writerow(["isbn", "title", "subtitle", "authors", "publisher", "publication_year", "description", "categories", "cover_image"])
    writer.writerow(["978-0-7475-3269-9", "Harry Potter and the Philosopher's Stone", "", "J.K. Rowling", "Bloomsbury", "1997", "A young wizard discovers his magical heritage.", "Fantasy", ""])
    return response