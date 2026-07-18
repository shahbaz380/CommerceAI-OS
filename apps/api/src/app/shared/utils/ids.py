"""ID generation helpers."""

from __future__ import annotations

import uuid


def new_uuid() -> uuid.UUID:
    """Generate a UUID4 (swap to UUID7 when stdlib/runtime supports widely)."""
    return uuid.uuid4()


def new_request_id() -> str:
    """Opaque request identifier for logs and client correlation."""
    return uuid.uuid4().hex
