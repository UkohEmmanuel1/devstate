from unittest.mock import Mock, patch
import jwt
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from core.models import ClerkProfile, Project, DevEvent, FocusSession, DomainAsset, HostingService, AISubscription

class ClerkAuthenticationTests(APITestCase):
    def test_missing_token_is_401(self):
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], "Bearer")

    @patch("core.authentication.jwks_client")
    def test_invalid_token_is_401(self, client_factory):
        client_factory.return_value.get_signing_key_from_jwt.return_value = Mock(key="public-key")
        with patch("core.authentication.jwt.decode", side_effect=jwt.InvalidTokenError("bad signature")):
            response = self.client.get("/api/projects/", HTTP_AUTHORIZATION="Bearer invalid")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response["WWW-Authenticate"], "Bearer")

    @patch("core.authentication.jwks_client")
    def test_valid_token_creates_local_user(self, client_factory):
        client_factory.return_value.get_signing_key_from_jwt.return_value = Mock(key="public-key")
        with patch("core.authentication.jwt.decode", return_value={"sub": "user_clerk_test", "iss": "https://issuer/", "azp": "http://localhost:3000", "exp": 9999999999}):
            response = self.client.get("/api/projects/", HTTP_AUTHORIZATION="Bearer valid")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ClerkProfile.objects.filter(clerk_user_id="user_clerk_test").exists())

class OwnershipIsolationTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user_a = User.objects.create_user(username="account-a")
        self.user_b = User.objects.create_user(username="account-b")
        ClerkProfile.objects.create(user=self.user_a, clerk_user_id="clerk_a")
        ClerkProfile.objects.create(user=self.user_b, clerk_user_id="clerk_b")
        Project.objects.create(owner=self.user_b, name="private", path="/private")
        DevEvent.objects.create(owner=self.user_b, source="test", title="private event")
        now = timezone.now()
        FocusSession.objects.create(owner=self.user_b, started_at=now, ends_at=now + timedelta(hours=1))
        self.domain = DomainAsset.objects.create(owner=self.user_b, domain_name="private.example")
        self.host = HostingService.objects.create(owner=self.user_b, name="private host")
        self.subscription = AISubscription.objects.create(owner=self.user_b, provider="private AI")

    def authenticate_as_a(self):
        self.client.force_authenticate(user=self.user_a)

    def test_user_a_cannot_list_user_b_records(self):
        self.authenticate_as_a()
        for url in ["/api/projects/", "/api/events/", "/api/domains/", "/api/hosting/", "/api/ai-subscriptions/"]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, [])

    def test_user_a_cannot_access_user_b_infrastructure_objects(self):
        self.authenticate_as_a()
        for url in [f"/api/domains/{self.domain.pk}/", f"/api/hosting/{self.host.pk}/", f"/api/ai-subscriptions/{self.subscription.pk}/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_focus_is_scoped_to_authenticated_user(self):
        self.authenticate_as_a()
        response = self.client.get("/api/focus/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["active"])

from core.views import is_public_http_target

class HostingTargetSafetyTests(APITestCase):
    @patch("core.views.socket.getaddrinfo")
    def test_loopback_target_is_rejected(self, resolver):
        resolver.return_value = [(2, 1, 6, "", ("127.0.0.1", 80))]
        self.assertFalse(is_public_http_target("http://localhost"))

    @override_settings(DEBUG=True)
    @patch("core.views.socket.getaddrinfo")
    def test_public_ip_target_is_allowed(self, resolver):
        resolver.return_value = [(2, 1, 6, "", ("8.8.8.8", 443))]
        self.assertTrue(is_public_http_target("https://status.example.com"))

    def test_non_http_scheme_is_rejected(self):
        self.assertFalse(is_public_http_target("file:///etc/passwd"))
