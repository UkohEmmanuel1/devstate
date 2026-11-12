from datetime import timedelta
import httpx
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import AISubscription, DomainAsset, HostingService, DevEvent

class Command(BaseCommand):
    help = "Notify about upcoming AI, domain and hosting renewals."

    def handle(self, *args, **options):
        now = timezone.now()
        due_items = []
        sources = [
            ("AI subscription", AISubscription.objects.filter(active=True, renews_at__isnull=False), "renews_at", None),
            ("Domain", DomainAsset.objects.filter(expires_at__isnull=False), "expires_at", 30),
            ("Hosting", HostingService.objects.filter(renewal_at__isnull=False), "renewal_at", 14),
        ]
        for label, queryset, date_field, default_days in sources:
            for item in queryset:
                renews_at = getattr(item, date_field)
                days_left = (renews_at - now).total_seconds() / 86400
                threshold = item.reminder_days if label == "AI subscription" else default_days
                if days_left <= threshold:
                    due_items.append((label, item, max(0, int(days_left)), renews_at))
        sent = 0
        for label, item, days_left, renews_at in due_items:
            name = getattr(item, "provider", None) or getattr(item, "domain_name", None) or item.name
            title = f"{label} renewal: {name}"
            message = f"{name} is due in {days_left} day(s), on {timezone.localtime(renews_at).strftime('%Y-%m-%d %H:%M %Z')}."
            already_logged = DevEvent.objects.filter(source="renewal-monitor", title=title, created_at__date=timezone.localdate()).exists()
            if already_logged:
                continue
            DevEvent.objects.create(source="renewal-monitor", title=title, message=message, priority=1)
            if settings.NTFY_TOPIC:
                headers = {"Title": title, "Priority": "4", "Tags": "warning"}
                if settings.NTFY_TOKEN:
                    headers["Authorization"] = "Bearer " + settings.NTFY_TOKEN
                try:
                    response = httpx.post(settings.NTFY_SERVER + "/" + settings.NTFY_TOPIC, content=message.encode(), headers=headers, timeout=10)
                    response.raise_for_status()
                    sent += 1
                except httpx.HTTPError as exc:
                    self.stderr.write(f"Notification failed for {name}: {exc}")
        self.stdout.write(self.style.SUCCESS(f"Checked renewals. {len(due_items)} due, {sent} phone notifications sent."))
