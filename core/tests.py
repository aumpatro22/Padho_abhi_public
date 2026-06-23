from django.test import TestCase
from django.conf import settings
import importlib
import os
import smartstudy.settings as project_settings

class CorsSettingsTest(TestCase):
    def test_cors_allow_all_origins_defaults_to_false(self):
        # By default in the test environment (unless set), it should be False
        # But we need to ensure the project settings logic respects the environment variable

        # Test default
        if 'CORS_ALLOW_ALL_ORIGINS' in os.environ:
            del os.environ['CORS_ALLOW_ALL_ORIGINS']
        importlib.reload(project_settings)
        self.assertFalse(project_settings.CORS_ALLOW_ALL_ORIGINS)

        # Test truthy values
        for val in ('true', '1', 'yes', 'True', 'YES'):
            os.environ['CORS_ALLOW_ALL_ORIGINS'] = val
            importlib.reload(project_settings)
            self.assertTrue(project_settings.CORS_ALLOW_ALL_ORIGINS)

        # Test falsy values
        for val in ('false', '0', 'no', 'False', 'NO', 'random_string'):
            os.environ['CORS_ALLOW_ALL_ORIGINS'] = val
            importlib.reload(project_settings)
            self.assertFalse(project_settings.CORS_ALLOW_ALL_ORIGINS)

        # Clean up
        if 'CORS_ALLOW_ALL_ORIGINS' in os.environ:
            del os.environ['CORS_ALLOW_ALL_ORIGINS']
