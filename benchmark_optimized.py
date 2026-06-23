import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartstudy.settings')
django.setup()

from django.db import connection, reset_queries
from core.models import Topic, Flashcard, Unit, Subject
from django.contrib.auth.models import User
from core.serializers import TopicSerializer
from django.db.models import Count

def setup_data():
    Topic.objects.all().delete()
    Unit.objects.all().delete()
    Subject.objects.all().delete()
    User.objects.all().delete()

    user = User.objects.create(username='testuser')
    subject = Subject.objects.create(name='Subject', code='SUB', user=user)
    unit = Unit.objects.create(name='Unit', unit_number=1, subject=subject)

    for i in range(50):
        topic = Topic.objects.create(name=f'Topic {i}', unit=unit)
        for j in range(5):
            Flashcard.objects.create(topic=topic, front_text=f'F {j}', back_text=f'B {j}')

def run_benchmark():
    reset_queries()
    start_time = time.time()

    topics = Topic.objects.annotate(flashcard_count_annotated=Count('flashcards'))
    # Assuming we modify serializer locally to read flashcard_count_annotated
    # Wait, we need to mock or change the real serializer to test properly.

if __name__ == '__main__':
    # We will modify the real serializer to use annotated if available!
    pass
