import csv
import io
from django.conf import settings
from django.contrib import messages


def log_action(actor, action, resource_type, resource_id, metadata=None):
    from audit.models import AuditLog

    AuditLog.objects.create(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id),
        metadata=metadata or {},
    )


def validate_csv_file(uploaded_file, expected_columns):
    _check_csv_size(uploaded_file)
    content = uploaded_file.read().decode("utf-8-sig")
    uploaded_file.seek(0)
    reader = csv.DictReader(io.StringIO(content))
    header = reader.fieldnames or []
    missing = [col for col in expected_columns if col not in header]
    return list(reader), missing


def parse_csv_upload(uploaded_file):
    _check_csv_size(uploaded_file)
    content = uploaded_file.read().decode("utf-8-sig")
    uploaded_file.seek(0)
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


def _check_csv_size(uploaded_file):
    max_size = getattr(settings, "MAX_CSV_UPLOAD_SIZE", 5 * 1024 * 1024)
    uploaded_file.seek(0, 2)
    size = uploaded_file.tell()
    uploaded_file.seek(0)
    if size > max_size:
        from django.core.exceptions import ValidationError
        raise ValidationError(f"CSV file exceeds maximum size of {max_size // (1024 * 1024)} MB.")