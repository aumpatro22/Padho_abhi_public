import os
from unittest.mock import patch
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Subject, Unit, Topic, Note, Mindmap, Flashcard, MCQQuestion, UserProfile


class SecuritySettingsTest(TestCase):
    def test_debug_is_false_by_default(self):
        """
        Ensure that the DEBUG setting defaults to False for security.
        """
        self.assertFalse(settings.DEBUG, "DEBUG should be False by default for security.")

        with patch.dict(os.environ, clear=True):
            debug_val = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')
            self.assertFalse(debug_val)


class TopicViewSetGenerateContentTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.profile = UserProfile.objects.get(user=self.user)
        self.client.force_authenticate(user=self.user)

        self.subject = Subject.objects.create(name='Computer Science', user=self.user)
        self.unit = Unit.objects.create(subject=self.subject, unit_number=1, name='Unit 1')
        self.topic = Topic.objects.create(unit=self.unit, name='Data Structures', order=1)
        self.url = f'/api/topics/{self.topic.id}/generate_content/'

    @patch('core.views.gemini_service.generate_all_content')
    def test_generate_content_success(self, mock_generate):
        mock_generate.return_value = {
            'notes': {
                'summary': 'Summary of Data Structures',
                'detailed_content': 'Detailed content about Data Structures',
                'analogies': ['Analogy 1'],
                'diagram_description': 'Diagram description'
            },
            'mindmap': {'root': 'Data Structures'},
            'flashcards': [
                {'front': 'What is array?', 'back': 'Contiguous memory collection'}
            ],
            'mcqs': [
                {
                    'question': 'What is time complexity of array lookup?',
                    'options': {'a': 'O(1)', 'b': 'O(n)', 'c': 'O(log n)', 'd': 'O(n^2)'},
                    'correct': 'a',
                    'explanation': 'Direct indexing access',
                    'difficulty': 'easy'
                }
            ],
            'usage': {'input': 100, 'output': 200}
        }

        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')

        # Assert objects created in DB
        self.assertTrue(Note.objects.filter(topic=self.topic).exists())
        self.assertTrue(Mindmap.objects.filter(topic=self.topic).exists())
        self.assertEqual(Flashcard.objects.filter(topic=self.topic).count(), 1)
        self.assertEqual(MCQQuestion.objects.filter(topic=self.topic).count(), 1)

    @patch('core.views.gemini_service.generate_all_content')
    def test_generate_content_rate_limit_error(self, mock_generate):
        mock_generate.return_value = {
            'notes': {'error': '429 Rate limit quota exceeded'}
        }

        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('quota exceeded', response.data['error'].lower())

    @patch('core.views.gemini_service.generate_all_content')
    def test_generate_content_general_ai_error(self, mock_generate):
        mock_generate.return_value = {
            'notes': {'error': 'Failed to parse JSON'}
        }

        response = self.client.post(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], 'AI generation failed')

    @patch('core.views.run_task_async')
    @patch('core.views.is_async_enabled', return_value=True)
    def test_generate_content_async(self, mock_async_enabled, mock_run_task):
        mock_run_task.return_value = (True, 'task-123')
        response = self.client.post(self.url, {'async': True}, format='json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'processing')
