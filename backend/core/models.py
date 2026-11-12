from django.db import models
class Project(models.Model):
 name=models.CharField(max_length=120); path=models.TextField(unique=True); branch=models.CharField(max_length=255,blank=True,null=True); commit=models.CharField(max_length=64,blank=True,null=True); dirty_paths=models.JSONField(default=list); last_scanned_at=models.DateTimeField(auto_now=True)
 class Meta: ordering=['name']
class DevEvent(models.Model):
 source=models.CharField(max_length=80); title=models.CharField(max_length=160); message=models.TextField(blank=True); priority=models.PositiveSmallIntegerField(default=2); created_at=models.DateTimeField(auto_now_add=True)
 class Meta: ordering=['-created_at']
class FocusSession(models.Model):
 started_at=models.DateTimeField(); ends_at=models.DateTimeField(); ended_at=models.DateTimeField(null=True,blank=True); active=models.BooleanField(default=True)
 class Meta: ordering=['-started_at']


class DomainAsset(models.Model):
    domain_name = models.CharField(max_length=253, unique=True)
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


class HostingService(models.Model):
    STATUS_CHOICES = [("active", "Active"), ("paused", "Paused"), ("unknown", "Unknown")]
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


class AISubscription(models.Model):
    BILLING_CHOICES = [("monthly", "Monthly"), ("annual", "Annual"), ("weekly", "Weekly"), ("other", "Other")]
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
