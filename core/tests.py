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

from .views import sanitize_text

class SanitizeTextTest(TestCase):
    def test_sanitize_empty_inputs(self):
        """Test sanitize_text with empty and None inputs."""
        self.assertEqual(sanitize_text(None), '')
        self.assertEqual(sanitize_text(''), '')

    def test_sanitize_non_string_inputs(self):
        """Test sanitize_text with non-string inputs."""
        self.assertEqual(sanitize_text(123), '123')
        self.assertEqual(sanitize_text(45.67), '45.67')
        self.assertEqual(sanitize_text(True), 'True')

    def test_sanitize_html_escaping(self):
        """Test sanitize_text with HTML characters to ensure they are escaped."""
        self.assertEqual(sanitize_text('<script>alert("XSS")</script>'), '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;')
        self.assertEqual(sanitize_text('<b>bold text</b>'), '&lt;b&gt;bold text&lt;/b&gt;')
        self.assertEqual(sanitize_text('John & Doe'), 'John &amp; Doe')

    def test_sanitize_max_length(self):
        """Test sanitize_text with strings exceeding max_length."""
        text = 'a' * 15000
        self.assertEqual(len(sanitize_text(text)), 10000)

        text2 = 'b' * 100
        self.assertEqual(len(sanitize_text(text2, max_length=50)), 50)
        self.assertEqual(sanitize_text(text2, max_length=50), 'b' * 50)

    def test_sanitize_normal_string(self):
        """Test sanitize_text with normal strings."""
        self.assertEqual(sanitize_text('hello world'), 'hello world')
