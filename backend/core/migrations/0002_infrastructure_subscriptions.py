# Infrastructure and recurring subscription records.
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial")]
    operations = [
        migrations.CreateModel(name="AISubscription", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("provider", models.CharField(max_length=120)),
            ("plan_name", models.CharField(blank=True, max_length=120)),
            ("price", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
            ("currency", models.CharField(default="USD", max_length=8)),
            ("billing_cycle", models.CharField(choices=[("monthly","Monthly"),("annual","Annual"),("weekly","Weekly"),("other","Other")], default="monthly", max_length=16)),
            ("renews_at", models.DateTimeField(blank=True, null=True)),
            ("reminder_days", models.PositiveSmallIntegerField(default=7)),
            ("management_url", models.URLField(blank=True)),
            ("active", models.BooleanField(default=True)),
            ("notes", models.TextField(blank=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ], options={"ordering":["renews_at","provider"]}),
        migrations.CreateModel(name="DomainAsset", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("domain_name", models.CharField(max_length=253, unique=True)),
            ("registrar", models.CharField(blank=True, max_length=120)),
            ("expires_at", models.DateTimeField(blank=True, null=True)),
            ("nameservers", models.JSONField(blank=True, default=list)),
            ("expected_dns", models.JSONField(blank=True, default=dict)),
            ("last_dns_check", models.DateTimeField(blank=True, null=True)),
            ("dns_status", models.CharField(default="unknown", max_length=32)),
            ("observed_dns", models.JSONField(blank=True, default=dict)),
            ("notes", models.TextField(blank=True)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
        ], options={"ordering":["domain_name"]}),
        migrations.CreateModel(name="HostingService", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=120)),
            ("provider", models.CharField(blank=True, max_length=120)),
            ("service_url", models.URLField(blank=True)),
            ("dashboard_url", models.URLField(blank=True)),
            ("renewal_at", models.DateTimeField(blank=True, null=True)),
            ("status", models.CharField(choices=[("active","Active"),("paused","Paused"),("unknown","Unknown")], default="unknown", max_length=16)),
            ("last_checked_at", models.DateTimeField(blank=True, null=True)),
            ("last_http_status", models.PositiveSmallIntegerField(blank=True, null=True)),
            ("notes", models.TextField(blank=True)),
        ], options={"ordering":["name"]}),
    ]
