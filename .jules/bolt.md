## 2025-03-05 - Django N+1 Query in Dashboard
**Learning:** In Django, iterating over a queryset that references foreign keys (like `p.topic.name` from a `UserProgress` queryset) without pre-fetching the related objects causes an N+1 query problem. This was heavily impacting the `dashboard` endpoint where it fetched all user progress records and then independently queried the topic for each record.
**Action:** Use `.select_related('topic')` on the `UserProgress` queryset to fetch the related topic data in a single SQL join, drastically reducing the number of database queries (from N queries to 1-2 queries) and improving response times.
## 2024-08-24 - Bulk Operations for Content Generation

**Learning:** Replaced consecutive `.create()` method calls within a loop with a batch approach that appends items to a list and stores them all together utilizing Django's `.bulk_create()` operation, which provides drastic improvements in database I/O overhead.

**Action:** Optimized `core/views.py` to use `bulk_create` when saving generated MCQs and Flashcards to mitigate an N+1 query vulnerability when inserting new AI-generated data into the db.
