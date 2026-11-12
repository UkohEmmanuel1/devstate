"""End-to-end Clerk JWT authentication and tenant-isolation tests.

All JWTs are signed locally with ephemeral RSA keys. The JWKS resolver is mocked,
so this suite never makes network requests and still exercises PyJWT's real
signature, issuer and time-claim validation.
"""
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from core.models import (
    AISubscription,
    ClerkProfile,
    DevEvent,
    DomainAsset,
    FocusSession,
    HostingService,
    Project,
)


class ClerkJWTAuthenticationTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_key = cls.private_key.public_key()
        cls.other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.jwks = patch("core.authentication.jwks_client")
        self.mock_jwks = self.jwks.start()
        self.addCleanup(self.jwks.stop)
        self.mock_jwks.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(
            key=self.public_key
        )

    def make_token(self, subject="user_clerk_a", **overrides):
        now = timezone.now()
        claims = {
            "sub": subject,
            "iss": "https://example.clerk.accounts.dev",
            "iat": int(now.timestamp()),
            "nbf": int((now - timedelta(seconds=5)).timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
        }
        claims.update(overrides)
        return jwt.encode(claims, self.private_key, algorithm="RS256", headers={"kid": "test-key"})

    def get_with_token(self, token):
        return self.client.get(
            "/api/projects/", HTTP_AUTHORIZATION=f"Bearer {token}"
        )

    def test_missing_authorization_header_returns_401_with_bearer_challenge(self):
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], "Bearer")

    def test_malformed_bearer_token_returns_401(self):
        response = self.get_with_token("not-a-jwt")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], "Bearer")

    def test_expired_clerk_token_returns_401(self):
        token = self.make_token(exp=int((timezone.now() - timedelta(minutes=2)).timestamp()))
        response = self.get_with_token(token)
        self.assertEqual(response.status_code, 401)

    def test_invalid_rsa_signature_returns_401(self):
        token = jwt.encode(
            {
                "sub": "user_clerk_a",
                "iss": "https://example.clerk.accounts.dev",
                "iat": int(timezone.now().timestamp()),
                "exp": int((timezone.now() + timedelta(minutes=5)).timestamp()),
            },
            self.other_private_key,
            algorithm="RS256",
            headers={"kid": "test-key"},
        )
        response = self.get_with_token(token)
        self.assertEqual(response.status_code, 401)

    def test_wrong_issuer_returns_401(self):
        token = self.make_token(iss="https://attacker.example")
        response = self.get_with_token(token)
        self.assertEqual(response.status_code, 401)

    def test_valid_clerk_token_provisions_local_user_and_profile(self):
        token = self.make_token()
        response = self.get_with_token(token)
        self.assertEqual(response.status_code, 200)
        profile = ClerkProfile.objects.select_related("user").get(clerk_user_id="user_clerk_a")
        self.assertTrue(profile.user.is_active)

    def test_valid_clerk_token_reuses_existing_profile_user(self):
        User = get_user_model()
        existing = User.objects.create_user(username="existing-clerk-account")
        ClerkProfile.objects.create(user=existing, clerk_user_id="user_clerk_a")
        response = self.get_with_token(self.make_token())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClerkProfile.objects.get(clerk_user_id="user_clerk_a").user_id, existing.pk)

    @override_settings(CLERK_AUTHORIZED_PARTIES=["https://trusted.example"])
    def test_untrusted_authorized_party_returns_401(self):
        token = self.make_token(azp="https://attacker.example")
        response = self.get_with_token(token)
        self.assertEqual(response.status_code, 401)


class ClerkTenantIsolationTests(ClerkJWTAuthenticationTests):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.user_a = User.objects.create_user(username="tenant-a")
        self.user_b = User.objects.create_user(username="tenant-b")
        ClerkProfile.objects.create(user=self.user_a, clerk_user_id="user_clerk_a")
        ClerkProfile.objects.create(user=self.user_b, clerk_user_id="user_clerk_b")
        now = timezone.now()
        self.project_b = Project.objects.create(owner=self.user_b, name="B private", path="/b/private")
        self.event_b = DevEvent.objects.create(owner=self.user_b, source="test", title="B private event")
        self.focus_b = FocusSession.objects.create(
            owner=self.user_b, started_at=now, ends_at=now + timedelta(hours=1), active=True
        )
        self.domain_b = DomainAsset.objects.create(owner=self.user_b, domain_name="b-private.example")
        self.host_b = HostingService.objects.create(owner=self.user_b, name="B private host")
        self.ai_b = AISubscription.objects.create(owner=self.user_b, provider="B private AI")

    def authenticate_a(self):
        return self.make_token(subject="user_clerk_a")

    def test_list_endpoints_only_return_authenticated_users_records(self):
        token = self.authenticate_a()
        urls = [
            "/api/projects/",
            "/api/events/",
            "/api/domains/",
            "/api/hosting/",
            "/api/ai-subscriptions/",
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, [])

    def test_user_a_cannot_read_update_or_delete_user_b_infrastructure_records(self):
        token = self.authenticate_a()
        records = [
            ("domains", self.domain_b.pk, {"notes": "attempted takeover"}),
            ("hosting", self.host_b.pk, {"notes": "attempted takeover"}),
            ("ai-subscriptions", self.ai_b.pk, {"notes": "attempted takeover"}),
        ]
        for collection, record_id, payload in records:
            url = f"/api/{collection}/{record_id}/"
            headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
            with self.subTest(method="GET", url=url):
                self.assertEqual(self.client.get(url, **headers).status_code, 404)
            with self.subTest(method="PATCH", url=url):
                self.assertEqual(self.client.patch(url, payload, format="json", **headers).status_code, 404)
            with self.subTest(method="DELETE", url=url):
                self.assertEqual(self.client.delete(url, **headers).status_code, 404)

    def test_project_and_event_lists_do_not_leak_foreign_records(self):
        token = self.authenticate_a()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        for url, private_value in [
            ("/api/projects/", "B private"),
            ("/api/events/", "B private event"),
        ]:
            response = self.client.get(url, **headers)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(private_value, str(response.data))

    def test_focus_endpoint_does_not_expose_another_users_active_session(self):
        response = self.client.get(
            "/api/focus/", HTTP_AUTHORIZATION=f"Bearer {self.authenticate_a()}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["active"])

    def test_user_a_can_create_own_event_and_cannot_spoof_owner(self):
        response = self.client.post(
            "/api/events/create/",
            {"source": "test", "title": "A event", "owner": self.user_b.pk},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.authenticate_a()}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DevEvent.objects.get(pk=response.data["id"]).owner_id, self.user_a.pk)

    def test_user_a_can_start_own_focus_session(self):
        response = self.client.post(
            "/api/focus/start/?hours=1",
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.authenticate_a()}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FocusSession.objects.get(pk=response.data["id"]).owner_id, self.user_a.pk)

    def test_infrastructure_create_assigns_owner_from_verified_clerk_subject(self):
        response = self.client.post(
            "/api/domains/",
            {"domain_name": "a-owned.example", "owner": self.user_b.pk},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.authenticate_a()}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(DomainAsset.objects.get(pk=response.data["id"]).owner_id, self.user_a.pk)

    def test_user_a_can_list_only_its_own_records_for_every_supported_resource(self):
        now = timezone.now()
        Project.objects.create(owner=self.user_a, name="A project", path="/a/project")
        DevEvent.objects.create(owner=self.user_a, source="test", title="A event")
        FocusSession.objects.create(
            owner=self.user_a, started_at=now, ends_at=now + timedelta(hours=1), active=True
        )
        DomainAsset.objects.create(owner=self.user_a, domain_name="a.example")
        HostingService.objects.create(owner=self.user_a, name="A host")
        AISubscription.objects.create(owner=self.user_a, provider="A AI")
        token = self.authenticate_a()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        expected = [
            ("/api/projects/", "name", "A project"),
            ("/api/events/", "title", "A event"),
            ("/api/domains/", "domain_name", "a.example"),
            ("/api/hosting/", "name", "A host"),
            ("/api/ai-subscriptions/", "provider", "A AI"),
        ]
        for url, field, value in expected:
            with self.subTest(url=url):
                response = self.client.get(url, **headers)
                self.assertEqual(response.status_code, 200)
                self.assertEqual([item[field] for item in response.data], [value])
        focus = self.client.get("/api/focus/", **headers)
        self.assertEqual(focus.status_code, 200)
        self.assertTrue(focus.data["active"])

    def test_user_a_cannot_end_user_b_focus_session(self):
        response = self.client.post(
            "/api/focus/end/",
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.authenticate_a()}",
        )
        self.assertEqual(response.status_code, 200)
        self.focus_b.refresh_from_db()
        self.assertTrue(self.focus_b.active)

    def test_project_and_event_detail_routes_do_not_expose_foreign_records(self):
        token = self.authenticate_a()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        for url in [f"/api/projects/{self.project_b.pk}/", f"/api/events/{self.event_b.pk}/"]:
            for method in ("get", "patch", "delete"):
                with self.subTest(url=url, method=method):
                    response = getattr(self.client, method)(url, {"title": "attempted takeover"}, format="json", **headers) if method == "patch" else getattr(self.client, method)(url, **headers)
                    self.assertIn(response.status_code, (404, 405))
