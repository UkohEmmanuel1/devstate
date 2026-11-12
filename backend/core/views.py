"""Authenticated API views and infrastructure operations."""
import hashlib
import hmac
import ipaddress
import json
import os
import socket
import subprocess
import uuid
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import httpx
from django.conf import settings
from django.db import DatabaseError, connection
from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousFileOperation
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import (
    action,
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import (
    AISubscription,
    DevEvent,
    DomainAsset,
    FocusSession,
    HostingService,
    Project,
)
from .throttling import (
    InfrastructureCheckRateThrottle,
    NotificationRateThrottle,
    ProjectScanRateThrottle,
    SnapshotRateThrottle,
)
from .serializers import (
    AISubscriptionSerializer,
    DomainAssetSerializer,
    EventSerializer,
    FocusSerializer,
    HostingServiceSerializer,
    ProjectSerializer,
)


def is_public_http_target(url):
    """Reject unsafe destinations; production requests must use an egress proxy.

    The proxy must resolve and validate the destination at connection time and
    block private, loopback, link-local, reserved and metadata-service networks.
    The preliminary DNS check here is defense in depth, not the sole SSRF control.
    """
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username
            or parsed.password
        ):
            return False
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        records = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        addresses = {ipaddress.ip_address(record[4][0]) for record in records}
        if not addresses or not all(address.is_global for address in addresses):
            return False
        if not settings.DEBUG and not settings.DEVSTATE_EGRESS_PROXY_URL:
            return False
        return True
    except (ValueError, OSError):
        return False


def request_public_http_target(url):
    """Perform a bounded request through the mandatory production egress proxy."""
    if not is_public_http_target(url):
        raise ValueError("Target is not permitted for server-side monitoring.")
    return httpx.get(
        url,
        timeout=httpx.Timeout(8.0, connect=4.0),
        follow_redirects=False,
        proxy=settings.DEVSTATE_EGRESS_PROXY_URL or None,
        trust_env=False,
    )


def user_topic(user):
    if not settings.NTFY_TOPIC_PREFIX or not settings.NTFY_TOPIC_SECRET:
        return ""
    suffix = hmac.new(
        settings.NTFY_TOPIC_SECRET.encode(),
        str(user.pk).encode(),
        hashlib.sha256,
    ).hexdigest()[:32]
    return settings.NTFY_TOPIC_PREFIX.rstrip("-") + "-" + suffix


def notify(user, title, message, priority=3):
    topic = user_topic(user)
    if not topic:
        return False
    headers = {
        "Title": title,
        "Priority": str(max(1, min(5, 5 - priority))),
    }
    if settings.NTFY_TOKEN:
        headers["Authorization"] = "Bearer " + settings.NTFY_TOKEN
    response = httpx.post(
        settings.NTFY_SERVER + "/" + topic,
        content=message.encode(),
        headers=headers,
        timeout=httpx.Timeout(8.0, connect=4.0),
        follow_redirects=False,
    )
    response.raise_for_status()
    return True


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return Response({"status": "unavailable"}, status=503)
    return Response({"status": "ok", "database": "ok"})


@api_view(["GET"])
def projects(request):
    return Response(
        ProjectSerializer(
            Project.objects.filter(owner=request.user), many=True
        ).data
    )


@api_view(["GET"])
def events(request):
    return Response(
        EventSerializer(
            DevEvent.objects.filter(owner=request.user)[:100], many=True
        ).data
    )


@api_view(["POST"])
def create_event(request):
    serializer = EventSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    event = serializer.save(owner=request.user)
    sent = False
    if event.priority <= 1:
        try:
            sent = notify(
                request.user, event.title, event.message or event.source, event.priority
            )
        except httpx.HTTPError:
            pass
    return Response(
        {**EventSerializer(event).data, "phone_notification_sent": sent},
        status=201,
    )


@api_view(["GET"])
def focus(request):
    now = timezone.now()
    FocusSession.objects.filter(
        owner=request.user, active=True, ends_at__lte=now
    ).update(active=False, ended_at=now)
    item = FocusSession.objects.filter(owner=request.user, active=True).first()
    return Response({"active": bool(item), **(FocusSerializer(item).data if item else {})})


@api_view(["POST"])
def focus_start(request):
    try:
        hours = int(request.query_params.get("hours", 6))
    except ValueError:
        return Response({"detail": "hours must be an integer"}, status=400)
    if not 1 <= hours <= 12:
        return Response({"detail": "hours must be between 1 and 12"}, status=400)

    # Lock the owning user row so simultaneous starts cannot create multiple
    # active sessions for the same account on PostgreSQL.
    User = get_user_model()
    with transaction.atomic():
        User.objects.select_for_update().get(pk=request.user.pk)
        now = timezone.now()
        FocusSession.objects.filter(owner=request.user, active=True).update(
            active=False, ended_at=now
        )
        item = FocusSession.objects.create(
            owner=request.user,
            started_at=now,
            ends_at=now + timedelta(hours=hours),
        )
    return Response(FocusSerializer(item).data, status=201)


@api_view(["POST"])
def focus_end(request):
    now = timezone.now()
    FocusSession.objects.filter(owner=request.user, active=True).update(
        active=False, ended_at=now
    )
    return Response({"active": False, "ended_at": now})


@api_view(["POST"])
@throttle_classes([NotificationRateThrottle])
def notification_test(request):
    if not user_topic(request.user):
        return Response(
            {"detail": "Phone notifications are not configured."}, status=409
        )
    try:
        notify(
            request.user,
            "DevState · Test",
            "Your private phone notification channel is connected.",
            2,
        )
        return Response({"accepted_by_ntfy": True})
    except httpx.HTTPError:
        return Response(
            {"detail": "Notification provider request failed."}, status=502
        )


def _scan_roots_for_user(user):
    templates = [
        value.strip()
        for value in os.getenv("DEVSTATE_PROJECTS_DIRS", "").split(";")
        if value.strip()
    ]
    roots = []
    for template in templates:
        if not settings.DEBUG and "{user_id}" not in template:
            continue
        expanded = Path(
            template.replace("{user_id}", str(user.pk))
        ).expanduser()
        try:
            if not settings.DEBUG:
                base_text = template.split("{user_id}", 1)[0]
                base = Path(base_text).expanduser().resolve(strict=True)
                account_root = base / str(user.pk)
                # Refuse account-root symlinks, including links to another
                # account's directory that would otherwise remain under base.
                if account_root.is_symlink() or not account_root.is_dir():
                    continue
                resolved = expanded.resolve(strict=True)
                resolved.relative_to(account_root.resolve(strict=True))
            else:
                resolved = expanded.resolve(strict=True)
            if not resolved.is_dir():
                continue
            roots.append(resolved)
        except (OSError, ValueError):
            continue
    return roots


def _git_output(repo_path, *args):
    env = os.environ.copy()
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
    })
    result = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}", *args],
        cwd=str(repo_path),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
        timeout=8,
    )
    return result.stdout.strip()


@api_view(["POST"])
@throttle_classes([ProjectScanRateThrottle])
def scan_projects(request):
    if not settings.DEBUG:
        return Response(
            {
                "detail": (
                    "Server-side repository scanning is disabled in production. "
                    "Use the authenticated DevState Desktop Agent when available."
                )
            },
            status=409,
        )
    roots = _scan_roots_for_user(request.user)
    found = []
    for root in roots:
        candidates = [root]
        try:
            for child in root.iterdir():
                if child.is_dir() and not child.is_symlink():
                    candidates.append(child)
                    if len(candidates) >= 101:
                        break
        except OSError:
            continue
        for candidate in candidates:
            try:
                if candidate.is_symlink():
                    continue
                path = candidate.resolve(strict=True)
                path.relative_to(root)
                git_dir = path / ".git"
                if not git_dir.exists() or git_dir.is_symlink():
                    continue
                if git_dir.is_file():
                    pointer = git_dir.read_text(encoding="utf-8")[:1024].strip()
                    if not pointer.startswith("gitdir:"):
                        continue
                    linked_git_dir = (path / pointer.split(":", 1)[1].strip()).resolve(strict=True)
                    linked_git_dir.relative_to(root)
                elif not git_dir.is_dir():
                    continue
                dirty = _git_output(path, "status", "--porcelain")
                obj, _ = Project.objects.update_or_create(
                    owner=request.user,
                    path=str(path),
                    defaults={
                        "name": path.name,
                        "branch": _git_output(path, "branch", "--show-current") or "detached",
                        "commit": _git_output(path, "rev-parse", "--short", "HEAD"),
                        "dirty_paths": [
                            line[3:] for line in dirty.splitlines() if line.strip()
                        ],
                    },
                )
                found.append(obj)
            except (
                OSError,
                ValueError,
                subprocess.SubprocessError,
                SuspiciousFileOperation,
            ):
                continue
    return Response(
        {"scanned": len(found), "projects": ProjectSerializer(found, many=True).data}
    )


@api_view(["POST"])
@throttle_classes([SnapshotRateThrottle])
def snapshots(request):
    """Store private recovery exports in S3-compatible object storage in production."""
    records = ProjectSerializer(
        Project.objects.filter(owner=request.user), many=True
    ).data
    payload = json.dumps(records, indent=2, default=str).encode("utf-8")
    object_key = (
        f"snapshots/{request.user.pk}/"
        f"{timezone.now().strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex}.json"
    )

    if settings.DEBUG:
        directory = Path(os.getenv("DEVSTATE_RECOVERY_DIR", "data/recovery")).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        target = (directory / object_key.rsplit("/", 1)[-1]).resolve()
        target.relative_to(directory)
        target.write_bytes(payload)
        return Response({"saved": len(records), "file": str(target.name)})

    bucket = settings.DEVSTATE_SNAPSHOT_BUCKET
    if not bucket:
        return Response(
            {"detail": "Private snapshot object storage is not configured."},
            status=503,
        )
    try:
        import boto3

        client = boto3.client(
            "s3",
            region_name=settings.DEVSTATE_SNAPSHOT_REGION or None,
            endpoint_url=settings.DEVSTATE_SNAPSHOT_ENDPOINT or None,
        )
        client.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=payload,
            ContentType="application/json",
            ServerSideEncryption="AES256",
        )
    except Exception:
        return Response(
            {"detail": "Snapshot storage is temporarily unavailable."},
            status=503,
        )
    return Response({"saved": len(records), "file": object_key})


class OwnedViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DomainAssetViewSet(OwnedViewSet):
    queryset = DomainAsset.objects.all()
    serializer_class = DomainAssetSerializer

    @action(detail=True, methods=["post"], throttle_classes=[InfrastructureCheckRateThrottle])
    def check_dns(self, request, pk=None):
        item = self.get_object()
        observed = {}
        try:
            observed["A"] = sorted({
                entry[4][0]
                for entry in socket.getaddrinfo(
                    item.domain_name, None, socket.AF_INET
                )
            })
            item.dns_status = "resolved"
            expected = item.expected_dns.get("A", [])
            if expected and not set(expected).issubset(set(observed["A"])):
                item.dns_status = "mismatch"
        except socket.gaierror:
            item.dns_status = "failed"
            observed["error"] = "DNS lookup failed"
        item.observed_dns = observed
        item.last_dns_check = timezone.now()
        item.save(update_fields=["dns_status", "observed_dns", "last_dns_check"])
        return Response(DomainAssetSerializer(item).data)


class HostingServiceViewSet(OwnedViewSet):
    queryset = HostingService.objects.all()
    serializer_class = HostingServiceSerializer

    @action(detail=True, methods=["post"], throttle_classes=[InfrastructureCheckRateThrottle])
    def check(self, request, pk=None):
        item = self.get_object()
        if not item.service_url:
            return Response(
                {"detail": "Add a service URL before checking uptime."}, status=400
            )
        try:
            response = request_public_http_target(item.service_url)
            item.last_http_status = response.status_code
            item.status = "active" if response.status_code < 500 else "paused"
        except ValueError:
            return Response(
                {"detail": "Target is not permitted for server-side monitoring."},
                status=400,
            )
        except httpx.HTTPError:
            item.last_http_status = None
            item.status = "paused"
        item.last_checked_at = timezone.now()
        item.save(update_fields=["last_http_status", "status", "last_checked_at"])
        return Response(HostingServiceSerializer(item).data)


class AISubscriptionViewSet(OwnedViewSet):
    queryset = AISubscription.objects.all()
    serializer_class = AISubscriptionSerializer


@api_view(["GET"])
def renewals(request):
    now = timezone.now()
    items = []
    for sub in AISubscription.objects.filter(
        owner=request.user, active=True, renews_at__isnull=False
    ):
        days = (sub.renews_at - now).total_seconds() / 86400
        items.append({
            "kind": "ai_subscription",
            "id": sub.id,
            "name": sub.provider,
            "renews_at": sub.renews_at,
            "days_remaining": max(0, round(days)),
            "due": days <= sub.reminder_days,
        })
    for domain in DomainAsset.objects.filter(
        owner=request.user, expires_at__isnull=False
    ):
        days = (domain.expires_at - now).total_seconds() / 86400
        items.append({
            "kind": "domain",
            "id": domain.id,
            "name": domain.domain_name,
            "renews_at": domain.expires_at,
            "days_remaining": max(0, round(days)),
            "due": days <= 30,
        })
    for host in HostingService.objects.filter(
        owner=request.user, renewal_at__isnull=False
    ):
        days = (host.renewal_at - now).total_seconds() / 86400
        items.append({
            "kind": "hosting",
            "id": host.id,
            "name": host.name,
            "renews_at": host.renewal_at,
            "days_remaining": max(0, round(days)),
            "due": days <= 14,
        })
    return Response(sorted(items, key=lambda item: item["days_remaining"]))


@api_view(["POST"])
@throttle_classes([InfrastructureCheckRateThrottle])
def check_infrastructure(request):
    domains = []
    hosts = []
    domain_queryset = DomainAsset.objects.filter(owner=request.user).order_by("pk")
    host_queryset = HostingService.objects.filter(owner=request.user).exclude(service_url="").order_by("pk")
    domain_total = domain_queryset.count()
    host_total = host_queryset.count()
    max_checks = 25
    for item in domain_queryset[:max_checks]:
        try:
            addresses = sorted({
                entry[4][0]
                for entry in socket.getaddrinfo(
                    item.domain_name, None, socket.AF_INET
                )
            })
            item.observed_dns = {"A": addresses}
            expected = item.expected_dns.get("A", [])
            item.dns_status = (
                "mismatch"
                if expected and not set(expected).issubset(set(addresses))
                else "resolved"
            )
        except socket.gaierror:
            item.observed_dns = {"error": "DNS lookup failed"}
            item.dns_status = "failed"
        item.last_dns_check = timezone.now()
        item.save(update_fields=["observed_dns", "dns_status", "last_dns_check"])
        domains.append({
            "domain": item.domain_name,
            "status": item.dns_status,
            "observed": item.observed_dns,
        })

    for item in host_queryset[:max_checks]:
        try:
            response = request_public_http_target(item.service_url)
            item.last_http_status = response.status_code
            item.status = "active" if response.status_code < 500 else "paused"
            error = None
        except ValueError:
            item.last_http_status = None
            item.status = "paused"
            error = "Blocked target: production egress proxy required or destination is non-public"
        except httpx.HTTPError:
            item.last_http_status = None
            item.status = "paused"
            error = "Hosting check failed"
        item.last_checked_at = timezone.now()
        item.save(update_fields=["last_http_status", "status", "last_checked_at"])
        hosts.append({
            "name": item.name,
            "status": item.status,
            "http_status": item.last_http_status,
            **({"error": error} if error else {}),
        })
    return Response({
        "domains": domains,
        "hosting": hosts,
        "checked_at": timezone.now(),
        "limit_per_resource": max_checks,
        "truncated": domain_total > max_checks or host_total > max_checks,
        "remaining": {
            "domains": max(0, domain_total - max_checks),
            "hosting": max(0, host_total - max_checks),
        },
    })
