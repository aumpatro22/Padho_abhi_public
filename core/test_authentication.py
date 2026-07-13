from django.test import TestCase
from core.authentication import _build_username

class BuildUsernameTest(TestCase):
    def test_sub_only(self):
        """Test building username with only 'sub' claim."""
        username = _build_username("12345", None)
        self.assertEqual(username, "neon_12345")

    def test_email_only(self):
        """Test building username with only 'email' claim."""
        username = _build_username(None, "john@example.com")
        self.assertEqual(username, "neon_john")

    def test_sub_and_email(self):
        """Test building username with both 'sub' and 'email' claims."""
        # It should prioritize sub over email based on implementation
        username = _build_username("12345", "john@example.com")
        self.assertEqual(username, "neon_12345")

    def test_neither_sub_nor_email(self):
        """Test building username with neither claim."""
        username = _build_username(None, None)
        self.assertEqual(username, "neon_user")

    def test_empty_string_sub(self):
        """Test building username with empty string 'sub'."""
        # Empty string evaluates to False in python boolean context
        username = _build_username("", "john@example.com")
        self.assertEqual(username, "neon_john")

    def test_empty_string_both(self):
        """Test building username with empty strings for both."""
        username = _build_username("", "")
        self.assertEqual(username, "neon_user")
