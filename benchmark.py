import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smartstudy.settings")
django.setup()

from django.contrib.auth.models import User
from core.models import Subject, Unit, Topic
from core.serializers import SubjectListSerializer
from django.db import connection, reset_queries
from django.db.models import Count

# Setup test data
user, _ = User.objects.get_or_create(username='benchmark_user')

# Benchmark using the new query logic
reset_queries()
start_time = time.time()

# This mirrors what SubjectViewSet.get_queryset does now
subjects = list(Subject.objects.filter(user=user).annotate(
    annotated_unit_count=Count('units', distinct=True),
    annotated_topic_count=Count('units__topics', distinct=True)
))
serializer = SubjectListSerializer(subjects, many=True)
data = serializer.data

end_time = time.time()
num_queries = len(connection.queries)

print(f"Improved Time: {end_time - start_time:.4f} seconds")
print(f"Number of queries: {num_queries}")
