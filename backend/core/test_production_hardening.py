import os
import tempfile
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import (
    AISubscription,
    ClerkProfile,
    DevEvent,
    FocusSession,
    RenewalNotice,
)
from core.views import _scan_roots_for_user, is_public_http_target


class ClerkProvisioningPolicyTests(TestCase):
    @override_settings(CLERK_AUTHORIZED_PARTIES=["https://app.example"])
    @patch("core.authentication.jwks_client")
    @patch("core.authentication.jwt.decode")
    def test_missing_authorized_party_is_rejected_when_allowlist_is_configured(
        self, decode, jwks_factory
    ):
        from rest_framework.test import APIClient

        jwks_factory.return_value.get_signing_key_from_jwt.return_value.key = "test-key"
        decode.return_value = {
            "sub": "user_missing_azp",
            "exp": int((timezone.now() + timedelta(minutes=5)).timestamp()),
            "iat": int(timezone.now().timestamp()),
            "iss": "https://example.clerk.accounts.dev",
        }
        response = APIClient().get(
            "/api/projects/", HTTP_AUTHORIZATION="Bearer test-token"
        )
        self.assertEqual(response.status_code, 401)
        self.assertFalse(
            ClerkProfile.objects.filter(clerk_user_id="user_missing_azp").exists()
        )


class FocusSessionIntegrityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="focus-owner")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_starting_a_new_focus_session_leaves_exactly_one_active_session(self):
        now = timezone.now()
        old = FocusSession.objects.create(
            owner=self.user,
            started_at=now - timedelta(hours=2),
            ends_at=now + timedelta(hours=1),
            active=True,
        )
        response = self.client.post("/api/focus/start/?hours=2", {}, format="json")
        self.assertEqual(response.status_code, 201)
        old.refresh_from_db()
        self.assertFalse(old.active)
        self.assertEqual(
            FocusSession.objects.filter(owner=self.user, active=True).count(), 1
        )


class ScannerPathIsolationTests(TestCase):
    @override_settings(DEBUG=False)
    def test_user_scan_root_must_resolve_inside_configured_base(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "accounts"
            user_root = base / "42" / "repos"
            user_root.mkdir(parents=True)
            outside = Path(temporary) / "outside"
            outside.mkdir()
            with patch.dict(
                os.environ,
                {"DEVSTATE_PROJECTS_DIRS": str(base) + "/{user_id}/repos"},
            ):
                user = type("User", (), {"pk": 42})()
                roots = _scan_roots_for_user(user)
            self.assertEqual(roots, [user_root.resolve()])

    @override_settings(DEBUG=False)
    def test_symlinked_scan_root_outside_account_base_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "accounts"
            base.mkdir()
            outside = Path(temporary) / "outside"
            outside.mkdir()
            (base / "42").symlink_to(outside, target_is_directory=True)
            with patch.dict(
                os.environ,
                {"DEVSTATE_PROJECTS_DIRS": str(base) + "/{user_id}/repos"},
            ):
                user = type("User", (), {"pk": 42})()
                self.assertEqual(_scan_roots_for_user(user), [])


class OutboundMonitoringPolicyTests(TestCase):
    @override_settings(DEBUG=False, DEVSTATE_EGRESS_PROXY_URL="")
    @patch("core.views.socket.getaddrinfo")
    def test_production_host_checks_require_controlled_egress_proxy(self, resolver):
        resolver.return_value = [(2, 1, 6, "", ("8.8.8.8", 443))]
        self.assertFalse(is_public_http_target("https://status.example.com"))

    @override_settings(
        DEBUG=False, DEVSTATE_EGRESS_PROXY_URL="http://egress-proxy.internal:3128"
    )
    @patch("core.views.socket.getaddrinfo")
    def test_production_host_check_accepts_public_resolution_with_proxy(self, resolver):
        resolver.return_value = [(2, 1, 6, "", ("8.8.8.8", 443))]
        self.assertTrue(is_public_http_target("https://status.example.com"))

    @override_settings(DEBUG=False, DEVSTATE_SNAPSHOT_BUCKET="")
    def test_production_snapshot_fails_closed_without_private_object_storage(self):
        user = get_user_model().objects.create_user(username="snapshot-owner")
        client = APIClient()
        client.force_authenticate(user)
        response = client.post("/api/snapshots/", {}, format="json")
        self.assertEqual(response.status_code, 503)


class RenewalIdempotencyTests(TestCase):
    def test_repeated_daily_renewal_job_does_not_duplicate_delivery(self):
        user = get_user_model().objects.create_user(username="renewal-owner")
        AISubscription.objects.create(
            owner=user,
            provider="Test AI",
            renews_at=timezone.now() + timedelta(days=2),
            reminder_days=7,
            active=True,
        )
        with patch(
            "core.management.commands.check_renewals.notify", return_value=True
        ) as notify_mock:
            call_command("check_renewals")
            call_command("check_renewals")

        self.assertEqual(RenewalNotice.objects.count(), 1)
        self.assertEqual(RenewalNotice.objects.get().status, "sent")
        self.assertEqual(
            DevEvent.objects.filter(owner=user, source="renewal-monitor").count(), 1
        )
        notify_mock.assert_called_once()

    @override_settings(DEBUG=False)
    def test_user_root_symlink_to_another_account_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary) / "accounts"
            other_root = base / "7" / "repos"
            other_root.mkdir(parents=True)
            (base / "42").symlink_to(base / "7", target_is_directory=True)
            with patch.dict(
                os.environ,
                {"DEVSTATE_PROJECTS_DIRS": str(base) + "/{user_id}/repos"},
            ):
                user = type("User", (), {"pk": 42})()
                self.assertEqual(_scan_roots_for_user(user), [])


class ReadinessEndpointTests(TestCase):
    def test_health_endpoint_is_public_and_checks_database(self):
        response = APIClient().get("/api/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["database"], "ok")
