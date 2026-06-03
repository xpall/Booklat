import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import BookCopy, CopyHistory
from books.models import Book
from .forms import CopyForm, CopyImportForm
from core.decorators import permission_required, any_permission_required
from core.utils import log_action, parse_csv_upload


def _generate_copy_id(isbn):
    last = BookCopy.objects.filter(copy_id__startswith=f"{isbn}#").order_by("-id").first()
    if last:
        num = int(last.copy_id.rsplit("#", 1)[-1]) + 1
    else:
        num = 1
    return f"{isbn}#{num:02d}"


@any_permission_required("copies.view")
def copy_list_view(request):
    query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")
    show_archived = request.GET.get("show_archived") == "1"
    copies = BookCopy.objects.select_related("book")
    if not show_archived:
        copies = copies.filter(is_archived=False)
    if query:
        copies = copies.filter(book__title__icontains=query) | copies.filter(copy_id__icontains=query)
    if status_filter:
        copies = copies.filter(status=status_filter)
    return render(request, "inventory/copy_list.html", {
        "copies": copies,
        "query": query,
        "status_filter": status_filter,
        "show_archived": show_archived,
        "status_choices": BookCopy.Status.choices,
    })


@any_permission_required("copies.view")
def copy_detail_view(request, copy_id):
    copy = get_object_or_404(BookCopy.objects.select_related("book"), copy_id=copy_id)
    history = copy.history.select_related("actor").all()
    return render(request, "inventory/copy_detail.html", {"copy": copy, "history": history})


@require_http_methods(["GET", "POST"])
@permission_required("copies.create")
def copy_create_view(request):
    if request.method == "POST":
        form = CopyForm(request.POST)
        if form.is_valid():
            copy = form.save(commit=False)
            copy.copy_id = _generate_copy_id(copy.book.isbn)
            copy.save()
            CopyHistory.objects.create(book_copy=copy, event="Created", actor=request.user)
            log_action(request.user, "COPY_CREATED", "BookCopy", copy.copy_id)
            messages.success(request, f"Copy {copy.copy_id} created.")
            return redirect("inventory:copy_detail", copy_id=copy.copy_id)
    else:
        form = CopyForm()
    return render(request, "inventory/copy_form.html", {"form": form, "title": "Create Copy"})


@require_http_methods(["GET", "POST"])
@permission_required("copies.update")
def copy_update_view(request, copy_id):
    copy = get_object_or_404(BookCopy, copy_id=copy_id)
    if request.method == "POST":
        form = CopyForm(request.POST, instance=copy)
        if form.is_valid():
            form.save()
            log_action(request.user, "COPY_UPDATED", "BookCopy", copy.copy_id)
            messages.success(request, f"Copy {copy.copy_id} updated.")
            return redirect("inventory:copy_detail", copy_id=copy.copy_id)
    else:
        form = CopyForm(instance=copy)
    return render(request, "inventory/copy_form.html", {"form": form, "title": f"Edit {copy.copy_id}"})


@require_http_methods(["POST"])
@permission_required("copies.update")
def copy_status_change_view(request, copy_id):
    copy = get_object_or_404(BookCopy, copy_id=copy_id)
    new_status = request.POST.get("status")
    notes = request.POST.get("notes", "")
    if new_status and new_status in dict(BookCopy.Status.choices):
        old_status = copy.get_status_display()
        copy.status = new_status
        copy.save()
        event = f"Status changed: {old_status} → {copy.get_status_display()}"
        CopyHistory.objects.create(book_copy=copy, event=event, notes=notes, actor=request.user)
        log_action(request.user, "COPY_STATUS_CHANGED", "BookCopy", copy.copy_id, metadata={
            "old_status": old_status,
            "new_status": copy.get_status_display(),
            "notes": notes,
        })
        messages.success(request, f"Copy {copy.copy_id} status updated.")
    return redirect("inventory:copy_detail", copy_id=copy.copy_id)


@require_http_methods(["POST"])
@permission_required("copies.update")
def copy_archive_view(request, copy_id):
    copy = get_object_or_404(BookCopy, copy_id=copy_id)
    copy.is_archived = True
    copy.status = BookCopy.Status.ARCHIVED
    copy.save()
    CopyHistory.objects.create(book_copy=copy, event="Archived", actor=request.user)
    log_action(request.user, "COPY_ARCHIVED", "BookCopy", copy.copy_id)
    messages.success(request, f"Copy {copy.copy_id} archived.")
    return redirect("inventory:copy_list")


@require_http_methods(["POST"])
@permission_required("copies.update")
def copy_unarchive_view(request, copy_id):
    copy = get_object_or_404(BookCopy, copy_id=copy_id)
    copy.is_archived = False
    copy.status = BookCopy.Status.AVAILABLE
    copy.save()
    CopyHistory.objects.create(book_copy=copy, event="Unarchived", actor=request.user)
    log_action(request.user, "COPY_UNARCHIVED", "BookCopy", copy.copy_id)
    messages.success(request, f"Copy {copy.copy_id} unarchived.")
    return redirect("inventory:copy_detail", copy_id=copy.copy_id)


@require_http_methods(["GET", "POST"])
@permission_required("system.import_data")
def copy_import_view(request):
    preview_data = None
    errors = []
    if request.method == "POST":
        if "preview" in request.POST:
            form = CopyImportForm(request.POST, request.FILES)
            if form.is_valid():
                records = parse_csv_upload(request.FILES["csv_file"])
                request.session["csv_import_records"] = records
                preview_data = records
        elif "confirm" in request.POST:
            records = request.session.pop("csv_import_records", [])
            if records:
                imported, errors = _import_copies(records, request.user)
                if imported:
                    messages.success(request, f"Imported {imported} copies.")
                    return redirect("inventory:copy_list")
                preview_data = records
            else:
                messages.error(request, "No records to import. Please upload the CSV file again.")
                return redirect("inventory:copy_import")
    else:
        form = CopyImportForm()
    return render(request, "inventory/import.html", {
        "form": form,
        "preview_data": preview_data,
        "errors": errors,
        "title": "Import Copies",
        "columns": ["ISBN", "Shelf Location", "Acquisition Date", "Notes"],
    })


def _import_copies(records, actor):
    errors = []
    imported = 0
    for i, r in enumerate(records, 1):
        isbn = r.get("isbn", "").strip()
        try:
            book = Book.objects.get(isbn=isbn, is_archived=False)
        except Book.DoesNotExist:
            errors.append(f"Row {i}: book with ISBN {isbn} not found.")
            continue
        try:
            copy = BookCopy(
                copy_id=_generate_copy_id(isbn),
                book=book,
                shelf_location=r.get("shelf_location", "").strip(),
                acquisition_date=r.get("acquisition_date") or None,
                notes=r.get("notes", "").strip(),
            )
            copy.save()
            CopyHistory.objects.create(book_copy=copy, event="Created (CSV import)", actor=actor)
            log_action(actor, "COPY_CREATED", "BookCopy", copy.copy_id, metadata={"source": "csv_import"})
            imported += 1
        except Exception as e:
            errors.append(f"Row {i}: {isbn} - {str(e)}")
    return imported, errors


@permission_required("system.import_data")
def copy_sample_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="copies_sample.csv"'
    writer = csv.writer(response)
    writer.writerow(["isbn", "shelf_location", "acquisition_date", "notes"])
    writer.writerow(["978-0-7475-3269-9", "A-01-02", "2024-01-15", "Good condition"])
    return response