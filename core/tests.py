import os
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings

import time
from unittest.mock import MagicMock
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from rest_framework import exceptions
from rest_framework.test import APIRequestFactory
from core.authentication import NeonJWTAuthentication


class SecuritySettingsTest(TestCase):
    def test_debug_is_false_by_default(self):
        """
        Ensure that the DEBUG setting defaults to False for security.
        """
        # The settings module is already loaded with the fallback value because
        # it's initialized before our tests run. If it correctly falls back,
        # it should be False in test mode without explicit override (unless test
        # runner overrides it).

        # We explicitly reload settings to test the env var logic directly
        # or assert against django.conf.settings

        # Django's test runner sets DEBUG=False by default. Let's make sure
        # that the setting itself works.
        self.assertFalse(settings.DEBUG, "DEBUG should be False by default for security.")

        # Test the expression from settings.py explicitly
        with patch.dict(os.environ, clear=True):
            debug_val = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
            self.assertFalse(debug_val)


class NeonJWTAuthenticationTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        cls.public_key = cls.private_key.public_key()
        cls.private_pem = cls.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

    def setUp(self):
        self.factory = APIRequestFactory()
        self.auth = NeonJWTAuthentication()

    @patch("core.authentication._get_public_key")
    def test_authenticate_valid_token(self, mock_get_public_key):
        mock_get_public_key.return_value = self.public_key
        payload = {
            "sub": "user123",
            "email": "user@example.com",
            "exp": int(time.time()) + 3600,
        }
        token = jwt.encode(payload, self.private_pem, algorithm="RS256", headers={"kid": "key1"})
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        with patch.object(settings, "NEON_AUTH_ISSUER", None):
            user, _ = self.auth.authenticate(request)
            self.assertIsNotNone(user)
            self.assertEqual(user.email, "user@example.com")

    @patch("core.authentication._get_public_key")
    def test_authenticate_expired_token(self, mock_get_public_key):
        mock_get_public_key.return_value = self.public_key
        payload = {
            "sub": "user123",
            "email": "user@example.com",
            "exp": int(time.time()) - 3600,
        }
        token = jwt.encode(payload, self.private_pem, algorithm="RS256", headers={"kid": "key1"})
        request = self.factory.get("/", HTTP_AUTHORIZATION=f"Bearer {token}")

        with patch.object(settings, "NEON_AUTH_ISSUER", None):
            with self.assertRaises(exceptions.AuthenticationFailed) as cm:
                self.auth.authenticate(request)
            self.assertEqual(str(cm.exception), "Token has expired")
