"""Seed announcements and Freedom Wall content."""

from __future__ import annotations

from datetime import timedelta

from announcements.models import Announcement
from freedom_wall.models import FreedomPost, FreedomPostUpvote

from demo.seeders.common import (
    DemoSeedError,
    clamp_past,
    datetime_days_ago,
    load_json,
)


def seed_announcements(users):
    announcements = []
    valid_statuses = dict(Announcement.Status.choices)

    for item in load_json("announcements.json"):
        author = users.get(item["created_by"])
        if author is None:
            raise DemoSeedError(
                f"Announcement references unknown user: {item['created_by']}"
            )
        if item["status"] not in valid_statuses:
            raise DemoSeedError(
                f"Announcement '{item['title']}' has invalid status: {item['status']}"
            )

        announcement, _ = Announcement.objects.update_or_create(
            title=item["title"],
            defaults={
                "content": item["content"],
                "status": item["status"],
                "created_by": author,
            },
        )
        created_at = datetime_days_ago(
            item.get("created_days_ago", 30), hour=9, minute=30
        )
        updated_at = datetime_days_ago(
            item.get("updated_days_ago", item.get("created_days_ago", 30)),
            hour=9,
            minute=45,
        )
        Announcement.objects.filter(pk=announcement.pk).update(
            created_at=created_at,
            updated_at=updated_at,
        )
        announcement.refresh_from_db(fields=["created_at", "updated_at"])
        announcements.append(announcement)

    return announcements


def seed_freedom_posts(users):
    posts = []
    valid_colors = dict(FreedomPost.STICKY_COLORS)
    valid_statuses = dict(FreedomPost.Status.choices)

    for item in load_json("freedom_posts.json"):
        user = users.get(item["user"])
        if user is None:
            raise DemoSeedError(
                f"Freedom post references unknown user: {item['user']}"
            )
        if item["color"] not in valid_colors:
            raise DemoSeedError(
                f"Freedom post has invalid color: {item['color']}"
            )
        if item["status"] not in valid_statuses:
            raise DemoSeedError(
                f"Freedom post has invalid status: {item['status']}"
            )
        if (
            item.get("processed_days_ago") is not None
            and item["processed_days_ago"] > item["created_days_ago"]
        ):
            raise DemoSeedError(
                "Freedom post was processed before it was created."
            )

        processed_by = None
        if item.get("processed_by"):
            processed_by = users.get(item["processed_by"])
            if processed_by is None:
                raise DemoSeedError(
                    "Freedom post references unknown moderator: "
                    f"{item['processed_by']}"
                )

        processed_at = None
        if item.get("processed_days_ago") is not None:
            processed_at = datetime_days_ago(
                item["processed_days_ago"], hour=16, minute=20
            )

        post, _ = FreedomPost.objects.update_or_create(
            user=user,
            content=item["content"],
            defaults={
                "pen_name": item.get("pen_name", ""),
                "color": item["color"],
                "status": item["status"],
                "processed_by": processed_by,
                "processed_at": processed_at,
                "rejection_reason": item.get("rejection_reason", ""),
            },
        )
        created_at = datetime_days_ago(item["created_days_ago"], hour=12, minute=10)
        FreedomPost.objects.filter(pk=post.pk).update(created_at=created_at)
        post.refresh_from_db(fields=["created_at", "processed_at", "status"])

        upvote_lrns = []
        for lrn in item.get("upvotes", []):
            if lrn not in users:
                raise DemoSeedError(
                    f"Freedom post upvote references unknown user: {lrn}"
                )
            if lrn not in upvote_lrns:
                upvote_lrns.append(lrn)

        FreedomPostUpvote.objects.filter(post=post).delete()
        if upvote_lrns:
            created_upvotes = FreedomPostUpvote.objects.bulk_create(
                [FreedomPostUpvote(post=post, user=users[lrn]) for lrn in upvote_lrns]
            )
            for upvote in created_upvotes:
                upvote.created_at = clamp_past(created_at + timedelta(hours=6))
            FreedomPostUpvote.objects.bulk_update(created_upvotes, ["created_at"])

        posts.append(post)

    return posts
