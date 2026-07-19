# Listing Lifecycle

| From | To |
|------|-----|
| draft | ready_for_review, archived |
| ready_for_review | approved, draft, archived |
| approved | scheduled, publishing, draft, archived |
| scheduled | publishing, approved, archived |
| publishing | published, failed |
| published | paused, ended, archived |
| paused | published, ended, archived |
| ended | archived, draft |
| failed | draft, archived |

Invalid transitions raise `INVALID_LISTING_STATUS_TRANSITION`.
