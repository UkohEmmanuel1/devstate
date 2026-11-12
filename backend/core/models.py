from django.conf import settings
from django.db import models
from django.db.models import Q


class ClerkProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clerk_profile",
    )
    clerk_user_id = models.CharField(max_length=255, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Project(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects"
    )
    name = models.CharField(max_length=120)
    path = models.TextField()
    branch = models.CharField(max_length=255, blank=True, null=True)
    commit = models.CharField(max_length=64, blank=True, null=True)
    dirty_paths = models.JSONField(default=list)
    last_scanned_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["owner", "path"], name="uniq_project_owner_path")
        ]


class DevEvent(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="dev_events"
    )
    source = models.CharField(max_length=80)
    title = models.CharField(max_length=160)
    message = models.TextField(blank=True)
    priority = models.PositiveSmallIntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"], name="event_owner_created_idx")
        ]


class FocusSession(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="focus_sessions"
    )
    started_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner"],
                condition=Q(active=True),
                name="uniq_active_focus_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["owner", "-started_at"], name="focus_owner_started_idx")
        ]


class DomainAsset(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="domain_assets"
    )
    domain_name = models.CharField(max_length=253)
    registrar = models.CharField(max_length=120, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    nameservers = models.JSONField(default=list, blank=True)
    expected_dns = models.JSONField(default=dict, blank=True)
    last_dns_check = models.DateTimeField(null=True, blank=True)
    dns_status = models.CharField(max_length=32, default="unknown")
    observed_dns = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["domain_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "domain_name"], name="uniq_domain_owner_name"
            )
        ]
        indexes = [
            models.Index(fields=["owner", "expires_at"], name="domain_owner_expiry_idx")
        ]


class HostingService(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("unknown", "Unknown"),
    ]
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosting_services"
    )
    name = models.CharField(max_length=120)
    provider = models.CharField(max_length=120, blank=True)
    service_url = models.URLField(blank=True)
    dashboard_url = models.URLField(blank=True)
    renewal_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="unknown")
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_http_status = models.PositiveSmallIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["owner", "renewal_at"], name="host_owner_renewal_idx")
        ]


class AISubscription(models.Model):
    BILLING_CHOICES = [
        ("monthly", "Monthly"),
        ("annual", "Annual"),
        ("weekly", "Weekly"),
        ("other", "Other"),
    ]
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_subscriptions"
    )
    provider = models.CharField(max_length=120)
    plan_name = models.CharField(max_length=120, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=8, default="USD")
    billing_cycle = models.CharField(max_length=16, choices=BILLING_CHOICES, default="monthly")
    renews_at = models.DateTimeField(null=True, blank=True)
    reminder_days = models.PositiveSmallIntegerField(default=7)
    management_url = models.URLField(blank=True)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["renews_at", "provider"]
        indexes = [
            models.Index(
                fields=["owner", "active", "renews_at"], name="ai_owner_renewal_idx"
            )
        ]


class RenewalNotice(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sending", "Sending"),
        ("sent", "Sent"),
    ]
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="renewal_notices",
    )
    resource_type = models.CharField(max_length=32)
    resource_id = models.PositiveBigIntegerField()
    renewal_at = models.DateTimeField()
    reminder_date = models.DateField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.CharField(max_length=240, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "resource_type", "resource_id", "renewal_at", "reminder_date"],
                name="uniq_daily_renewal_notice",
            )
        ]
        indexes = [
            models.Index(fields=["status", "updated_at"], name="renewal_status_updated_idx")
        ]
