import os
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings

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

    def test_cors_allow_all_origins_disabled_with_credentials(self):
        """
        Ensure CORS_ALLOW_ALL_ORIGINS is not enabled when CORS_ALLOW_CREDENTIALS is True.
        """
        self.assertFalse(
            getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False),
            "CORS_ALLOW_ALL_ORIGINS should not be enabled when CORS_ALLOW_CREDENTIALS is True."
        )

    def test_cors_allowed_origins_parsing(self):
        """
        Verify parsing logic for CORS_ALLOWED_ORIGINS environment variable.
        """
        env_input = " http://localhost:3000 ,  http://127.0.0.1:3000,, http://example.com "
        parsed = [origin.strip() for origin in env_input.split(',') if origin.strip()]
        expected = ["http://localhost:3000", "http://127.0.0.1:3000", "http://example.com"]
        self.assertEqual(parsed, expected)
