from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import Announcement
from .forms import AnnouncementForm
from core.decorators import permission_required, any_permission_required
from core.utils import log_action


@any_permission_required("announcements.view")
def list_view(request):
    announcements = Announcement.objects.all().select_related("created_by")
    return render(request, "announcements/list.html", {
        "announcements": announcements,
    })


@require_http_methods(["GET", "POST"])
@permission_required("announcements.create")
def create_view(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = Announcement.objects.create(
                title=form.cleaned_data["title"],
                content=form.cleaned_data["content"],
                created_by=request.user,
            )
            log_action(request.user, "ANNOUNCEMENT_CREATED", "Announcement", str(announcement.pk), metadata={
                "title": announcement.title,
            })
            messages.success(request, "Announcement created.")
            return redirect("announcements:list")
    else:
        form = AnnouncementForm()

    return render(request, "announcements/create.html", {
        "form": form,
    })


@require_http_methods(["GET", "POST"])
@permission_required("announcements.update")
def update_view(request, announcement_id):
    announcement = get_object_or_404(Announcement, pk=announcement_id)

    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement.title = form.cleaned_data["title"]
            announcement.content = form.cleaned_data["content"]
            announcement.save()
            log_action(request.user, "ANNOUNCEMENT_UPDATED", "Announcement", str(announcement.pk), metadata={
                "title": announcement.title,
            })
            messages.success(request, "Announcement updated.")
            return redirect("announcements:list")
    else:
        form = AnnouncementForm(initial={
            "title": announcement.title,
            "content": announcement.content,
        })

    return render(request, "announcements/update.html", {
        "form": form,
        "announcement": announcement,
    })


@require_http_methods(["POST"])
@permission_required("announcements.archive")
def archive_view(request, announcement_id):
    announcement = get_object_or_404(Announcement, pk=announcement_id)
    if announcement.status == Announcement.Status.ARCHIVED:
        messages.error(request, "Announcement is already archived.")
        return redirect("announcements:list")

    announcement.archive(request.user)
    log_action(request.user, "ANNOUNCEMENT_ARCHIVED", "Announcement", str(announcement.pk), metadata={
        "title": announcement.title,
    })
    messages.success(request, "Announcement archived.")
    return redirect("announcements:list")
