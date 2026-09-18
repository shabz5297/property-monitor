"""
A fake property source for local development.

Why this exists: none of the major UK portals currently offer a free,
clearly-permitted way to pull live listings (Zoopla's old public API
was retired; Rightmove/OnTheMarket restrict scraping in their terms).
This lets you build and demo the *entire* pipeline -- dedup, matching,
notifications, API, dashboard -- without touching that grey area.

When you're ready to plug in a real, permitted source (e.g. HM Land
Registry Price Paid Data, or a specific agent site whose robots.txt
you've checked yourself), write a new class next to this one that
implements PropertySource, and swap it in main.py. Nothing else
in the app needs to change.
"""
from __future__ import annotations

import random
from typing import Iterable

from .models import Property, PropertyType
from .sources.base import PropertySource

_STREETS = [
    "Sturry Road", "Wincheap", "North Lane", "St Dunstans",
    "Old Dover Road", "Whitstable Road", "Nunnery Fields",
]
_TYPES = list(PropertyType)


class MockSource(PropertySource):
    """Generates a random-but-plausible batch of listings each call.

    Re-running fetch_listings() will sometimes repeat previous IDs and
    sometimes produce new ones -- deliberately, so you can exercise the
    dedup logic (Phase 2) against something that behaves like a real feed.
    """

    name = "mock"

    def __init__(self, seed: int | None = None, pool_size: int = 40):
        self._rng = random.Random(seed)
        self._pool_size = pool_size

    def fetch_listings(self, location: str) -> Iterable[Property]:
        # Pretend the "source" has a stable pool of listing IDs, and each
        # check returns a random subset -- similar to how a real portal's
        # search results shift between polls.
        n = self._rng.randint(3, 8)
        chosen_ids = self._rng.sample(range(1, self._pool_size + 1), n)

        for listing_num in chosen_ids:
            # Deterministic-ish per ID so the same ID tends to regenerate
            # similar (not identical) details, like a real listing would.
            local_rng = random.Random(listing_num)
            bedrooms = local_rng.randint(1, 5)
            ptype = local_rng.choice(_TYPES)
            street = local_rng.choice(_STREETS)
            price = local_rng.randint(150, 650) * 1000

            yield Property(
                source_name=self.name,
                source_id=str(listing_num),
                title=f"{bedrooms} Bed {ptype.value.title()}",
                price_gbp=price,
                location=f"{street}, {location}",
                bedrooms=bedrooms,
                property_type=ptype,
                url=f"https://example-mock-source.invalid/listing/{listing_num}",
            )
