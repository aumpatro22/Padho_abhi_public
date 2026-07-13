## 2025-03-05 - Django N+1 Query in Dashboard
**Learning:** In Django, iterating over a queryset that references foreign keys (like `p.topic.name` from a `UserProgress` queryset) without pre-fetching the related objects causes an N+1 query problem. This was heavily impacting the `dashboard` endpoint where it fetched all user progress records and then independently queried the topic for each record.
**Action:** Use `.select_related('topic')` on the `UserProgress` queryset to fetch the related topic data in a single SQL join, drastically reducing the number of database queries (from N queries to 1-2 queries) and improving response times.
## 2024-05-18 - Optimize bulk creation in Django

**Learning:** Replaced individual model instance saves in a loop with a single `bulk_create` call to mitigate N+1 insertions. This dramatically reduced execution time from 0.26 seconds to 0.01 seconds (22x improvement).
**Action:** Always prefer `bulk_create` in Django for inserting multiple rows to optimize database performance, particularly when generating lists of records.
