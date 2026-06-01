import csv
import io
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
    content = uploaded_file.read().decode("utf-8-sig")
    uploaded_file.seek(0)
    reader = csv.DictReader(io.StringIO(content))
    header = reader.fieldnames or []
    missing = [col for col in expected_columns if col not in header]
    return list(reader), missing


def parse_csv_upload(uploaded_file):
    content = uploaded_file.read().decode("utf-8-sig")
    uploaded_file.seek(0)
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)