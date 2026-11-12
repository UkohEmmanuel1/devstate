# Generated for DevState's initial Django data model.
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="DevEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source", models.CharField(max_length=80)),
                ("title", models.CharField(max_length=160)),
                ("message", models.TextField(blank=True)),
                ("priority", models.PositiveSmallIntegerField(default=2)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="FocusSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField()),
                ("ends_at", models.DateTimeField()),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("active", models.BooleanField(default=True)),
            ],
            options={"ordering": ["-started_at"]},
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("path", models.TextField(unique=True)),
                ("branch", models.CharField(blank=True, max_length=255, null=True)),
                ("commit", models.CharField(blank=True, max_length=64, null=True)),
                ("dirty_paths", models.JSONField(default=list)),
                ("last_scanned_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["name"]},
        ),
    ]
