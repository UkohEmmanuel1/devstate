from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_data_integrity_and_indexes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RenewalNotice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("resource_type", models.CharField(max_length=32)),
                ("resource_id", models.PositiveBigIntegerField()),
                ("renewal_at", models.DateTimeField()),
                ("reminder_date", models.DateField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("sending", "Sending"), ("sent", "Sent")], default="pending", max_length=16)),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("last_error", models.CharField(blank=True, max_length=240)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="renewal_notices", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="renewalnotice",
            constraint=models.UniqueConstraint(
                fields=("owner", "resource_type", "resource_id", "renewal_at", "reminder_date"),
                name="uniq_daily_renewal_notice",
            ),
        ),
        migrations.AddIndex(
            model_name="renewalnotice",
            index=models.Index(fields=["status", "updated_at"], name="renewal_status_updated_idx"),
        ),
    ]
