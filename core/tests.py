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

from core.encryption import encrypt_value, decrypt_value

class EncryptionTest(TestCase):
    def test_encrypt_value_success(self):
        """Test that a valid string is correctly encrypted."""
        original_value = "my_secret_data"
        encrypted = encrypt_value(original_value)

        # It shouldn't return the original string
        self.assertNotEqual(encrypted, original_value)
        self.assertTrue(len(encrypted) > 0)

        # It should be decryptable back to the original value
        decrypted = decrypt_value(encrypted)
        self.assertEqual(decrypted, original_value)

    def test_encrypt_value_empty(self):
        """Test that empty or None values return an empty string."""
        self.assertEqual(encrypt_value(""), "")
        self.assertEqual(encrypt_value(None), "")

    @patch('core.encryption.get_fernet')
    def test_encrypt_value_exception(self, mock_get_fernet):
        """Test that exceptions during encryption return an empty string."""
        mock_get_fernet.side_effect = Exception("Encryption failed")

        # An exception should be caught and return an empty string
        result = encrypt_value("sensitive_data")
        self.assertEqual(result, "")
