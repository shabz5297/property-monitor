"""
Phase 1 entry point.

Runs the full flow from the brief's diagram once:

    New listing found -> Already in database? -> (no) Save
        -> Check saved searches -> Does it match? -> (yes) Send alert

For Phase 1 the "database" is the in-memory ListingStore and the
"notification" is a console message -- both get upgraded in later
phases (Postgres in Phase 2, email in Phase 4) without this flow logic
changing.
"""
from __future__ import annotations

from property_monitor.utils.models import Property, PropertyType, SavedSearch
from property_monitor.store import ListingStore
from mock_source import MockSource

def notify(prop: Property, matched_search: SavedSearch) -> None:
    """Stand-in for Phase 4's email notifications."""
    print(
        f"\n🚨 NEW PROPERTY FOUND\n"
        f"{prop.title} — {prop.location}\n"
        f"£{prop.price_gbp:,}\n"
        f"Matches your: {matched_search.name}\n"
        f"[View Property] {prop.url}\n"
    )


def run_check(source, store: ListingStore, searches: list[SavedSearch], location: str) -> None:
    listings = source.check(location)
    print(f"[{source.name}] fetched {len(listings)} listings for '{location}'")

    for prop in listings:

        if store.has_seen(prop):
            continue  # not new -> ignore
        store.remember(prop)  # save it

        for search in searches:
            if search.matches(prop):
                notify(prop, search)


def main() -> None:
    source = MockSource(seed=None)
    store = ListingStore()

    searches = [
        SavedSearch(
            name="Canterbury Houses",
            location="Canterbury",
            max_price_gbp=300_000,
            min_bedrooms=2,
            property_type=PropertyType.HOUSE,
        ),
    ]

    print("Property Monitor — Phase 1 (mock source)\n")

    # Simulate a few polling cycles, like a scheduled job would trigger.
    for cycle in range(1, 6):
        print(f"--- check cycle {cycle} ---")
        run_check(source, store, searches, location="Canterbury")

    print(f"\nTotal unique listings stored: {len(store)}")


if __name__ == "__main__":
    main()
