"""
Core data model for Property Monitor.

Every source-specific scraper must normalise its raw data into this
shape before it goes anywhere near the database or the matching logic.
That's what lets us add new sources later without touching the rest
of the app (see brief: "Data normalisation").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class PropertyType(str, Enum):
    HOUSE = "house"
    FLAT = "flat"
    BUNGALOW = "bungalow"
    LAND = "land"
    OTHER = "other"


@dataclass(frozen=True)
class Property:
    """A single, normalised property listing.

    `source_id` + `source_name` together form the natural external key
    (see normalize.make_listing_id) used for deduplication.
    """

    source_name: str          # e.g. "mock", "landregistry"
    source_id: str            # the ID as it exists on that source
    title: str
    price_gbp: int
    location: str
    bedrooms: Optional[int]
    property_type: PropertyType
    url: str
    first_seen: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def listing_id(self) -> str:
        """Stable unique identifier used for dedup across the whole app."""
        return f"{self.source_name}:{self.source_id}"

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["property_type"] = self.property_type.value
        d["first_seen"] = self.first_seen.isoformat()
        d["listing_id"] = self.listing_id
        return d


@dataclass(frozen=True)
class SavedSearch:
    """A user's saved search criteria (brief section 2: Saved Searches)."""

    name: str
    location: str
    max_price_gbp: Optional[int] = None
    min_bedrooms: Optional[int] = None
    property_type: Optional[PropertyType] = None

    def matches(self, prop: Property) -> bool:
        """Brief section 2: Property Matching."""
        if self.location.lower() not in prop.location.lower():
            return False
        if self.max_price_gbp is not None and prop.price_gbp > self.max_price_gbp:
            return False
        if self.min_bedrooms is not None:
            if prop.bedrooms is None or prop.bedrooms < self.min_bedrooms:
                return False
        if self.property_type is not None and prop.property_type != self.property_type:
            return False
        return True
