"""
Minimal in-memory "already seen" store.

This is deliberately the simplest thing that could work, standing in
for the Postgres-backed store from Phase 2 of the brief. The interface
(has_seen / remember) is what matters -- swap the body for a real DB
later without touching main.py's flow logic.
"""
from __future__ import annotations

from property_monitor.models import Property


class ListingStore:
    def __init__(self):
        self._seen_ids: set[str] = set()

    def has_seen(self, prop: Property) -> bool:
        return prop.listing_id in self._seen_ids

    def remember(self, prop: Property) -> None:
        self._seen_ids.add(prop.listing_id)

    def __len__(self) -> int:
        return len(self._seen_ids)
