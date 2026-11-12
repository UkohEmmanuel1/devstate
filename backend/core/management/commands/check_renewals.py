"""Idempotently enqueue and deliver renewal reminders."""
import httpx
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    AISubscription,
    DevEvent,
    DomainAsset,
    HostingService,
    RenewalNotice,
)
from core.views import notify


class Command(BaseCommand):
    help = "Notify account owners about upcoming renewals."

    def handle(self, *args, **options):
        now = timezone.now()
        today = timezone.localdate()
        sources = [
            (
                "ai_subscription",
                "AI subscription",
                AISubscription.objects.filter(active=True, renews_at__isnull=False),
                "renews_at",
                None,
            ),
            (
                "domain",
                "Domain",
                DomainAsset.objects.filter(expires_at__isnull=False),
                "expires_at",
                30,
            ),
            (
                "hosting",
                "Hosting",
                HostingService.objects.filter(renewal_at__isnull=False),
                "renewal_at",
                14,
            ),
        ]
        due = sent = retried = 0

        for resource_type, label, queryset, date_field, default_days in sources:
            for item in queryset.select_related("owner").iterator():
                renewal_at = getattr(item, date_field)
                days_remaining = (renewal_at - now).total_seconds() / 86400
                threshold = (
                    item.reminder_days if default_days is None else default_days
                )
                if days_remaining > threshold:
                    continue

                due += 1
                name = (
                    getattr(item, "provider", None)
                    or getattr(item, "domain_name", None)
                    or item.name
                )
                title = f"{label} renewal: {name}"[:160]
                message = (
                    f"{name} is due in {max(0, int(days_remaining))} day(s), "
                    f"on {timezone.localtime(renewal_at).strftime('%Y-%m-%d %H:%M %Z')}."
                )

                with transaction.atomic():
                    notice, _ = RenewalNotice.objects.get_or_create(
                        owner=item.owner,
                        resource_type=resource_type,
                        resource_id=item.pk,
                        renewal_at=renewal_at,
                        reminder_date=today,
                    )
                    notice = RenewalNotice.objects.select_for_update().get(pk=notice.pk)
                    if notice.status == "sent":
                        continue
                    if (
                        notice.status == "sending"
                        and notice.updated_at > now - timedelta(minutes=10)
                    ):
                        continue

                    retried += int(notice.attempts > 0)
                    notice.status = "sending"
                    notice.attempts += 1
                    notice.last_error = ""
                    notice.save(update_fields=[
                        "status", "attempts", "last_error", "updated_at"
                    ])

                    event_exists = DevEvent.objects.filter(
                        owner=item.owner,
                        source="renewal-monitor",
                        title=title,
                        created_at__date=today,
                    ).exists()
                    if not event_exists:
                        DevEvent.objects.create(
                            owner=item.owner,
                            source="renewal-monitor",
                            title=title,
                            message=message,
                            priority=1,
                        )

                try:
                    delivered = notify(item.owner, title, message, 2)
                    if delivered:
                        sent += 1
                        status = "sent"
                        error = ""
                    else:
                        status = "pending"
                        error = "Notification provider is not configured."
                except httpx.HTTPError as exc:
                    status = "pending"
                    error = type(exc).__name__

                RenewalNotice.objects.filter(pk=notice.pk).update(
                    status=status,
                    last_error=error[:240],
                    updated_at=timezone.now(),
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Checked renewals. {due} due, {sent} delivered, "
                f"{retried} retry attempts."
            )
        )
