import csv
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Book, Category
from .forms import BookForm, CategoryForm, BookImportForm
from inventory.forms import CopyForm
from inventory.models import BookCopy, CopyHistory
from inventory.views import _generate_copy_id
from core.decorators import permission_required, any_permission_required
from core.utils import log_action, parse_csv_upload


@any_permission_required("books.view")
def book_list_view(request):
    query = request.GET.get("q", "")
    category_id = request.GET.get("category", "")
    filter_val = request.GET.get("filter", "")
    show_archived = request.GET.get("show_archived") == "1"
    books = Book.objects.all()
    if show_archived:
        books = books.filter(is_archived=True)
    else:
        books = books.filter(is_archived=False)
    if filter_val == "new":
        books = books.order_by("-created_at")
    if query:
        books = books.filter(title__icontains=query) | books.filter(authors__icontains=query) | books.filter(isbn__icontains=query)
    if category_id:
        books = books.filter(categories__id=category_id)
    books = books.prefetch_related("categories").distinct()
    all_categories = Category.objects.filter(is_archived=False)
    return render(request, "books/book_list.html", {
        "books": books, "query": query, "show_archived": show_archived,
        "categories": all_categories, "selected_category": category_id,
        "filter": filter_val,
    })


@any_permission_required("books.view")
def book_detail_view(request, isbn):
    book = get_object_or_404(Book, isbn=isbn)
    copies = book.copies.all() if book.is_archived else book.copies.filter(is_archived=False)
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
            return redirect("books:book_detail", isbn=book.isbn)
    else:
        form = BookForm()
    return render(request, "books/book_form.html", {"form": form, "title": "Create Book"})


@require_http_methods(["GET", "POST"])
@permission_required("books.update")
def book_update_view(request, isbn):
    book = get_object_or_404(Book, isbn=isbn)
    if request.method == "POST":
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            log_action(request.user, "BOOK_UPDATED", "Book", book.isbn)
            messages.success(request, f"Book '{book.title}' updated.")
            return redirect("books:book_detail", isbn=book.isbn)
    else:
        form = BookForm(instance=book)
    return render(request, "books/book_form.html", {"form": form, "title": f"Edit {book.title}"})


@require_http_methods(["POST"])
@permission_required("books.archive")
def book_archive_view(request, isbn):
    book = get_object_or_404(Book, isbn=isbn)
    book.is_archived = True
    book.save()
    log_action(request.user, "BOOK_ARCHIVED", "Book", book.isbn)
    messages.success(request, f"Book '{book.title}' archived.")
    return redirect("books:book_list")


@require_http_methods(["POST"])
@permission_required("books.archive")
def book_unarchive_view(request, isbn):
    book = get_object_or_404(Book, isbn=isbn)
    book.is_archived = False
    book.save()
    log_action(request.user, "BOOK_UNARCHIVED", "Book", book.isbn)
    messages.success(request, f"Book '{book.title}' unarchived.")
    return redirect("books:book_detail", isbn=book.isbn)


@require_http_methods(["GET", "POST"])
@permission_required("copies.create")
def book_add_copy_view(request, isbn):
    book = get_object_or_404(Book, isbn=isbn)
    if request.method == "POST":
        form = CopyForm(request.POST)
        if form.is_valid():
            copy = form.save(commit=False)
            copy.copy_id = _generate_copy_id(book.isbn)
            copy.book = book
            copy.save()
            CopyHistory.objects.create(book_copy=copy, event="Created", actor=request.user)
            log_action(request.user, "COPY_CREATED", "BookCopy", copy.copy_id)
            messages.success(request, f"Copy {copy.copy_id} created for '{book.title}'.")
            return redirect("books:book_detail", isbn=book.isbn)
    else:
        form = CopyForm(initial={"book": book})
    return render(request, "books/book_copy_form.html", {
        "form": form,
        "book": book,
        "title": f"Add Copy for {book.title}",
    })


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
                cover_image=r.get("cover_image", "").strip(),
            )
            book.save()
            cat_string = r.get("categories", "").strip()
            if cat_string:
                cat_names = [c.strip() for c in cat_string.split(",") if c.strip()]
                for cat_name in cat_names:
                    category, _ = Category.objects.get_or_create(name=cat_name)
                    book.categories.add(category)
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


@any_permission_required("books.view")
def book_search_json(request):
    q = request.GET.get("q", "").strip()
    books = Book.objects.filter(is_archived=False)
    if q:
        books = books.filter(title__icontains=q) | books.filter(isbn__icontains=q)
    books = books.distinct()[:20]
    results = [{"id": b.pk, "isbn": b.isbn, "title": b.title, "authors": b.authors} for b in books]
    return JsonResponse({"results": results})


@permission_required("categories.manage")
def category_list_view(request):
    show_archived = request.GET.get("show_archived") == "1"
    categories = Category.objects.all()
    if show_archived:
        categories = categories.filter(is_archived=True)
    else:
        categories = categories.filter(is_archived=False)
    return render(request, "books/category_list.html", {
        "categories": categories, "show_archived": show_archived,
    })


@require_http_methods(["GET", "POST"])
@permission_required("categories.manage")
def category_create_view(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            log_action(request.user, "CATEGORY_CREATED", "Category", category.id)
            messages.success(request, f"Category '{category.name}' created.")
            return redirect("books:category_list")
    else:
        form = CategoryForm()
    return render(request, "books/category_form.html", {"form": form, "title": "Create Category"})


@require_http_methods(["GET", "POST"])
@permission_required("categories.manage")
def category_update_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            log_action(request.user, "CATEGORY_UPDATED", "Category", category.id)
            messages.success(request, f"Category '{category.name}' updated.")
            return redirect("books:category_list")
    else:
        form = CategoryForm(instance=category)
    return render(request, "books/category_form.html", {"form": form, "title": f"Edit {category.name}"})


@require_http_methods(["POST"])
@permission_required("categories.manage")
def category_archive_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_archived = True
    category.save()
    log_action(request.user, "CATEGORY_ARCHIVED", "Category", category.id)
    messages.success(request, f"Category '{category.name}' archived.")
    return redirect("books:category_list")


@require_http_methods(["POST"])
@permission_required("categories.manage")
def category_unarchive_view(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_archived = False
    category.save()
    log_action(request.user, "CATEGORY_UNARCHIVED", "Category", category.id)
    messages.success(request, f"Category '{category.name}' unarchived.")
    return redirect("books:category_list")