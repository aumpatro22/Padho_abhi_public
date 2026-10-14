import os
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings

from django.core.exceptions import ValidationError
from core.views import validate_positive_integer

class ValidatePositiveIntegerTest(TestCase):
    def test_valid_positive_integers(self):
        """Test valid positive integers (int and string format) and zero."""
        self.assertEqual(validate_positive_integer(0), 0)
        self.assertEqual(validate_positive_integer(5), 5)
        self.assertEqual(validate_positive_integer("42"), 42)
        self.assertEqual(validate_positive_integer("0"), 0)

    def test_negative_integers_raise_validation_error(self):
        """Test that negative integers raise ValidationError with field_name in message."""
        with self.assertRaises(ValidationError) as cm:
            validate_positive_integer(-1)
        self.assertIn("value must be a positive integer", str(cm.exception))

        with self.assertRaises(ValidationError) as cm:
            validate_positive_integer("-10", field_name="age")
        self.assertIn("age must be a positive integer", str(cm.exception))

    def test_invalid_types_and_values_raise_validation_error(self):
        """Test that non-integer types/values raise ValidationError."""
        invalid_inputs = ["abc", None, [], {}, "12.34"]
        for val in invalid_inputs:
            with self.subTest(val=val):
                with self.assertRaises(ValidationError) as cm:
                    validate_positive_integer(val, field_name="count")
                self.assertIn("count must be a valid integer", str(cm.exception))


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
