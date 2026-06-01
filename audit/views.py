import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from .models import AuditLog
from core.decorators import permission_required


@permission_required("audit.view")
def audit_list_view(request):
    logs = AuditLog.objects.select_related("actor")
    action_filter = request.GET.get("action", "")
    resource_filter = request.GET.get("resource_type", "")
    if action_filter:
        logs = logs.filter(action=action_filter)
    if resource_filter:
        logs = logs.filter(resource_type=resource_filter)
    logs = logs[:200]
    actions = AuditLog.objects.values_list("action", flat=True).distinct().order_by("action")
    resource_types = AuditLog.objects.values_list("resource_type", flat=True).distinct().order_by("resource_type")
    return render(request, "audit/log_list.html", {
        "logs": logs,
        "action_filter": action_filter,
        "resource_filter": resource_filter,
        "actions": actions,
        "resource_types": resource_types,
    })


@permission_required("audit.view")
def audit_detail_view(request, log_id):
    log = AuditLog.objects.select_related("actor").get(pk=log_id)
    return render(request, "audit/log_detail.html", {"log": log})


@permission_required("system.export_data")
def audit_export_view(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
    writer = csv.writer(response)
    writer.writerow(["Timestamp", "Actor LRN", "Action", "Resource Type", "Resource ID"])
    for log in AuditLog.objects.select_related("actor").iterator():
        writer.writerow([
            log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            log.actor.lrn if log.actor else "",
            log.action,
            log.resource_type,
            log.resource_id,
        ])
    return response