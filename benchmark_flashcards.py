import os
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartstudy.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Subject, Unit, Topic, Flashcard

# Clean up
User.objects.filter(username='testuser').delete()

# Setup
user = User.objects.create_user('testuser', 'test@example.com', 'password')
subject = Subject.objects.create(user=user, name='Test Subject')
unit = Unit.objects.create(subject=subject, unit_number=1, name='Test Unit')
topic = Topic.objects.create(unit=unit, name='Test Topic', order=1)

flashcards_data = [{'front': f'Front {i}', 'back': f'Back {i}'} for i in range(100)]

# Benchmark looping
topic.flashcards.all().delete()
start_time = time.time()
for fc in flashcards_data:
    Flashcard.objects.create(
        topic=topic,
        front_text=fc.get('front', ''),
        back_text=fc.get('back', '')
    )
loop_time = time.time() - start_time
print(f"Loop time for 100 inserts: {loop_time:.4f} seconds")

# Benchmark bulk_create
topic.flashcards.all().delete()
start_time = time.time()
flashcard_objs = [
    Flashcard(
        topic=topic,
        front_text=fc.get('front', ''),
        back_text=fc.get('back', '')
    )
    for fc in flashcards_data
]
Flashcard.objects.bulk_create(flashcard_objs)
bulk_time = time.time() - start_time
print(f"Bulk create time for 100 inserts: {bulk_time:.4f} seconds")
