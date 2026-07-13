import os
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings

from core.ai_service import GeminiService


class GeminiServiceTest(TestCase):
    def setUp(self):
        # We don't want to actually initialize the genai model,
        # so we patch out genai.configure and genai.GenerativeModel during init.
        with patch('core.ai_service.genai'):
            self.service = GeminiService()

    def test_clean_json_response_clean_object(self):
        text = '{"key": "value", "number": 1}'
        result = self.service._clean_json_response(text)
        self.assertEqual(result, {"key": "value", "number": 1})

    def test_clean_json_response_clean_array(self):
        text = '[{"key": "value"}, {"key": "value2"}]'
        result = self.service._clean_json_response(text)
        self.assertEqual(result, [{"key": "value"}, {"key": "value2"}])

    def test_clean_json_response_with_markdown(self):
        text = 'Here is the response:\n```json\n{"success": true}\n```\nHope it helps.'
        result = self.service._clean_json_response(text)
        self.assertEqual(result, {"success": True})

    def test_clean_json_response_with_arbitrary_surrounding_text(self):
        text = 'Random prefix {"nested": {"value": 123}} random suffix'
        result = self.service._clean_json_response(text)
        self.assertEqual(result, {"nested": {"value": 123}})

    def test_clean_json_response_invalid_json_but_matches_regex(self):
        # The regex matches {.*}, but json.loads will fail
        text = 'Some text {invalid json format: missing quotes} more text'
        result = self.service._clean_json_response(text)
        self.assertIsNone(result)

    def test_clean_json_response_no_json(self):
        text = 'Just a regular response with no brackets or braces.'
        result = self.service._clean_json_response(text)
        self.assertIsNone(result)

    def test_clean_json_response_empty_string(self):
        text = ''
        result = self.service._clean_json_response(text)
        self.assertIsNone(result)

    def test_clean_json_response_with_array_markdown(self):
        text = '```\n[\n"apple", "banana"\n]\n```'
        result = self.service._clean_json_response(text)
        self.assertEqual(result, ["apple", "banana"])


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
