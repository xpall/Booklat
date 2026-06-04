from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import models
from django_ratelimit.decorators import ratelimit
from .models import FreedomPost, FreedomPostUpvote
from .forms import CreatePostForm, ProcessPostForm
from core.decorators import permission_required, any_permission_required
from core.utils import log_action


@any_permission_required("freedom_wall.view")
def post_list_view(request):
    sort = request.GET.get("sort", "newest")
    posts = FreedomPost.objects.filter(
        status=FreedomPost.Status.APPROVED
    ).select_related("user").annotate(upvote_count=models.Count("upvotes"))

    if sort == "upvotes":
        posts = posts.order_by("-upvote_count", "-created_at")
    else:
        posts = posts.order_by("-created_at")

    user_upvoted_ids = set()
    if request.user.is_authenticated:
        user_upvoted_ids = set(
            FreedomPostUpvote.objects.filter(
                user=request.user,
                post__in=posts,
            ).values_list("post_id", flat=True)
        )

    pending_posts = []
    if request.user.is_admin or request.user.is_staff_user:
        pending_posts = FreedomPost.objects.filter(
            status=FreedomPost.Status.PENDING
        ).select_related("user")
    return render(request, "freedom_wall/post_list.html", {
        "posts": posts,
        "pending_posts": pending_posts,
        "user_upvoted_ids": user_upvoted_ids,
        "current_sort": sort,
    })


@require_http_methods(["GET", "POST"])
@permission_required("freedom_wall.create")
@ratelimit(key="user_or_ip", rate="10/m", method="POST")
def post_create_view(request):
    was_limited = getattr(request, "limited", False)
    if was_limited:
        messages.error(request, "Too many requests. Please wait a minute and try again.")
        return redirect("freedom_wall:post_list")

    today = timezone.localdate()
    already_posted = FreedomPost.objects.filter(
        user=request.user,
        created_at__date=today,
    ).exists()
    if already_posted:
        messages.error(request, "You have already posted today. Come back tomorrow.")
        return redirect("freedom_wall:post_list")

    if request.method == "POST":
        form = CreatePostForm(request.POST)
        if form.is_valid():
            post = FreedomPost(
                user=request.user,
                pen_name=form.cleaned_data["pen_name"].strip(),
                content=form.cleaned_data["content"],
            )
            post.randomize_color()
            post.save()
            log_action(request.user, "FREEDOM_POST_CREATED", "FreedomPost", str(post.pk), metadata={
                "user_lrn": request.user.lrn,
                "pen_name": post.pen_name,
            })
            messages.success(request, "Your note has been submitted for approval.")
            return redirect("freedom_wall:post_list")
    else:
        form = CreatePostForm()

    return render(request, "freedom_wall/post_create.html", {
        "form": form,
    })


@permission_required("freedom_wall.approve")
def post_pending_view(request):
    posts = FreedomPost.objects.filter(
        status=FreedomPost.Status.PENDING
    ).select_related("user")
    return render(request, "freedom_wall/post_pending.html", {
        "posts": posts,
    })


@require_http_methods(["GET", "POST"])
@permission_required("freedom_wall.approve")
def post_process_view(request, post_id):
    post = get_object_or_404(
        FreedomPost.objects.select_related("user"), pk=post_id
    )
    if post.status != FreedomPost.Status.PENDING:
        messages.error(request, "Only pending posts can be processed.")
        return redirect("freedom_wall:post_list")

    if request.method == "POST":
        action = request.POST.get("action", "")
        if action in ("approve", "reject"):
            post.processed_by = request.user
            post.processed_at = timezone.now()
            if action == "approve":
                post.status = FreedomPost.Status.APPROVED
                post.rejection_reason = ""
                post.save()
                log_action(request.user, "FREEDOM_POST_APPROVED", "FreedomPost", str(post.pk), metadata={
                    "author_lrn": post.user.lrn,
                })
                messages.success(request, "Post approved and published to the wall.")
            elif action == "reject":
                post.status = FreedomPost.Status.REJECTED
                post.rejection_reason = request.POST.get("rejection_reason", "")
                post.save()
                log_action(request.user, "FREEDOM_POST_REJECTED", "FreedomPost", str(post.pk), metadata={
                    "author_lrn": post.user.lrn,
                    "reason": post.rejection_reason,
                })
                messages.success(request, "Post rejected.")
            return redirect("freedom_wall:post_list")
    else:
        form = ProcessPostForm()

    return render(request, "freedom_wall/post_process.html", {
        "form": form,
        "post_obj": post,
    })


@require_http_methods(["POST"])
@permission_required("freedom_wall.approve")
def post_delete_view(request, post_id):
    post = get_object_or_404(FreedomPost, pk=post_id)
    if post.status == FreedomPost.Status.DELETED:
        messages.error(request, "Post is already deleted.")
        return redirect("freedom_wall:post_list")
    post.status = FreedomPost.Status.DELETED
    post.processed_by = request.user
    post.processed_at = timezone.now()
    post.save()
    log_action(request.user, "FREEDOM_POST_DELETED", "FreedomPost", str(post.pk), metadata={
        "author_lrn": post.user.lrn,
    })
    messages.success(request, "Post removed from the wall.")
    return redirect("freedom_wall:post_list")


@require_http_methods(["POST"])
@any_permission_required("freedom_wall.view")
def post_upvote_view(request, post_id):
    post = get_object_or_404(
        FreedomPost, pk=post_id, status=FreedomPost.Status.APPROVED
    )
    upvote, created = FreedomPostUpvote.objects.get_or_create(
        post=post, user=request.user,
    )
    if not created:
        upvote.delete()

    return redirect(request.META.get("HTTP_REFERER", reverse("freedom_wall:post_list")))
