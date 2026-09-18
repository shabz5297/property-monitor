"""
Common interface every property source must implement.

This is the seam the brief talks about under "Scraping / Data Collection":
    Property Source -> Scraper -> Raw Listing -> Normalise -> Property Object

Adding a new source later means writing one new class here, not touching
anything downstream (dedup, matching, notifications, API).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from .models import Property


class PropertySource(ABC):
    """Base class for all property sources (mock, Land Registry, etc.)."""

    #: short machine name used as the first half of Property.listing_id
    name: str

    @abstractmethod
    def fetch_listings(self, location: str) -> Iterable[Property]:
        """Return the current listings for a location as Property objects.

        Implementations own their own fetching + normalisation. This
        method should already return clean Property instances -- no raw
        HTML/JSON should leak past this boundary.
        """
        raise NotImplementedError

    def check(self, location: str) -> list[Property]:
        """Wrapper around fetch_listings with basic error containment.

        Brief section 5, "Reliability": a source being down shouldn't
        crash the whole monitoring run. Real sources should override
        fetch_listings, not this method.
        """
        try:
            return list(self.fetch_listings(location))
        except Exception as exc:  # noqa: BLE001 - deliberately broad at this boundary
            print(f"[{self.name}] source check failed: {exc}")
            return []
