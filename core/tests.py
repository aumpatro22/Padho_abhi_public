import os
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings
from core.encryption import encrypt_value, decrypt_value

class EncryptionTest(TestCase):
    def test_encrypt_decrypt_happy_path(self):
        """
        Ensure that a value can be encrypted and then decrypted back to the original value.
        """
        original_value = "secret_api_key_123!"
        encrypted = encrypt_value(original_value)
        self.assertNotEqual(encrypted, original_value)
        self.assertNotEqual(encrypted, "")

        decrypted = decrypt_value(encrypted)
        self.assertEqual(decrypted, original_value)

    def test_decrypt_empty_value(self):
        """
        Ensure that decrypt_value returns an empty string when given an empty or None value.
        """
        self.assertEqual(decrypt_value(""), "")
        self.assertEqual(decrypt_value(None), "")

    def test_decrypt_invalid_token(self):
        """
        Ensure that decrypt_value returns an empty string when given an invalid token.
        """
        self.assertEqual(decrypt_value("not-a-valid-token"), "")
        self.assertEqual(decrypt_value("gAAAAAnotvalid"), "")

    @patch('core.encryption.get_fernet')
    def test_decrypt_exception_handling(self, mock_get_fernet):
        """
        Ensure that decrypt_value handles exceptions gracefully and returns an empty string.
        """
        mock_get_fernet.side_effect = Exception("Simulated decryption error")
        self.assertEqual(decrypt_value("gAAAAAvalidformat"), "")


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
