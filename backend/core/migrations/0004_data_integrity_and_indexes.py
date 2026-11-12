"""Database-level invariants and indexes for multi-tenant workloads."""
from django.db import migrations, models
from django.db.models import Q
from django.utils import timezone


def keep_one_active_focus_session(apps, schema_editor):
    FocusSession = apps.get_model("core", "FocusSession")
    alias = schema_editor.connection.alias
    owner_ids = (
        FocusSession.objects.using(alias)
        .filter(active=True)
        .values_list("owner_id", flat=True)
        .distinct()
    )
    now = timezone.now()
    for owner_id in owner_ids.iterator():
        active = list(
            FocusSession.objects.using(alias)
            .filter(owner_id=owner_id, active=True)
            .order_by("-started_at", "-pk")
        )
        for stale in active[1:]:
            FocusSession.objects.using(alias).filter(pk=stale.pk).update(
                active=False,
                ended_at=stale.ended_at or now,
            )


class Migration(migrations.Migration):
    dependencies = [("core", "0003_user_ownership")]

    operations = [
        migrations.RunPython(
            keep_one_active_focus_session,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="focussession",
            constraint=models.UniqueConstraint(
                fields=("owner",),
                condition=Q(active=True),
                name="uniq_active_focus_per_user",
            ),
        ),
        migrations.AddIndex(
            model_name="devevent",
            index=models.Index(
                fields=["owner", "-created_at"],
                name="event_owner_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="focussession",
            index=models.Index(
                fields=["owner", "-started_at"],
                name="focus_owner_started_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="domainasset",
            index=models.Index(
                fields=["owner", "expires_at"],
                name="domain_owner_expiry_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="hostingservice",
            index=models.Index(
                fields=["owner", "renewal_at"],
                name="host_owner_renewal_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="aisubscription",
            index=models.Index(
                fields=["owner", "active", "renews_at"],
                name="ai_owner_renewal_idx",
            ),
        ),
    ]
