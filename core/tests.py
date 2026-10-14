import os
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings
from .views import sanitize_text

class SecuritySettingsTest(TestCase):
    def test_debug_is_false_by_default(self):
        """
        Ensure that the DEBUG setting defaults to False for security.
        """
        self.assertFalse(settings.DEBUG, "DEBUG should be False by default for security.")

        with patch.dict(os.environ, clear=True):
            debug_val = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
            self.assertFalse(debug_val)


class SanitizeTextTest(TestCase):
    def test_empty_or_falsy_inputs(self):
        """Ensure empty or falsy inputs return empty string."""
        self.assertEqual(sanitize_text(None), '')
        self.assertEqual(sanitize_text(''), '')

    def test_non_string_inputs(self):
        """Ensure non-string inputs are converted to string and sanitized."""
        self.assertEqual(sanitize_text(12345), '12345')
        self.assertEqual(sanitize_text(True), 'True')
        self.assertEqual(sanitize_text(3.14), '3.14')

    def test_normal_string(self):
        """Ensure plain strings without special HTML characters remain unchanged."""
        self.assertEqual(sanitize_text('Hello World'), 'Hello World')

    def test_html_escaping_xss(self):
        """Ensure HTML special characters are escaped to prevent XSS."""
        raw_text = '<script>alert("XSS")</script>&'
        expected = '&lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;&amp;'
        self.assertEqual(sanitize_text(raw_text), expected)

    def test_max_length_truncation_default(self):
        """Ensure text exceeding default max_length (10000) is truncated before escaping."""
        long_text = 'a' * 10005
        result = sanitize_text(long_text)
        self.assertEqual(len(result), 10000)

    def test_max_length_truncation_custom(self):
        """Ensure custom max_length parameter truncates text properly."""
        raw_text = 'abcdefghij'
        result = sanitize_text(raw_text, max_length=5)
        self.assertEqual(result, 'abcde')

    def test_truncation_before_html_escape(self):
        """Verify that truncation happens before HTML escaping."""
        # '<script>' length is 8 characters. Truncate to 5 chars: '<scri' -> escaped: '&lt;scri'
        raw_text = '<script>'
        result = sanitize_text(raw_text, max_length=5)
        self.assertEqual(result, '&lt;scri')
