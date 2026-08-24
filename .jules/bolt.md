## 2023-10-24 - Bulk creation for flashcards performance boost
**Learning:** Instantiating multiple models and then using `bulk_create` reduces database queries significantly compared to individual `.create()` operations in a loop.
**Action:** Use `bulk_create` for performance optimizations involving mass insertions.
