"""
A handful of tests for the two riskiest bits of Phase 1: dedup and
matching. Run with: pytest property_monitor/test_core.py
"""
from property_monitor import Property, PropertyType, SavedSearch
from property_monitor import ListingStore


def _prop(**overrides) -> Property:
    defaults = dict(
        source_name="mock",
        source_id="1",
        title="2 Bed House",
        price_gbp=285_000,
        location="Sturry Road, Canterbury",
        bedrooms=2,
        property_type=PropertyType.HOUSE,
        url="https://example.invalid/1",
    )
    defaults.update(overrides)
    return Property(**defaults)


def test_dedup_ignores_repeat_listing():
    store = ListingStore()
    p = _prop()
    assert not store.has_seen(p)
    store.remember(p)
    assert store.has_seen(p)
    # a listing with the same source+id is the same listing even if
    # price/title text differs slightly between polls
    same_id_different_price = _prop(price_gbp=290_000)
    assert store.has_seen(same_id_different_price)


def test_dedup_treats_different_sources_as_different_listings():
    store = ListingStore()
    store.remember(_prop(source_name="mock"))
    assert not store.has_seen(_prop(source_name="landregistry"))


def test_search_matches_within_criteria():
    search = SavedSearch(
        name="Canterbury Houses",
        location="Canterbury",
        max_price_gbp=300_000,
        min_bedrooms=2,
        property_type=PropertyType.HOUSE,
    )
    assert search.matches(_prop())


def test_search_rejects_over_budget():
    search = SavedSearch(name="x", location="Canterbury", max_price_gbp=200_000)
    assert not search.matches(_prop(price_gbp=285_000))


def test_search_rejects_too_few_bedrooms():
    search = SavedSearch(name="x", location="Canterbury", min_bedrooms=3)
    assert not search.matches(_prop(bedrooms=2))


def test_search_rejects_wrong_location():
    search = SavedSearch(name="x", location="London")
    assert not search.matches(_prop(location="Sturry Road, Canterbury"))


def test_search_rejects_wrong_property_type():
    search = SavedSearch(name="x", location="Canterbury", property_type=PropertyType.FLAT)
    assert not search.matches(_prop(property_type=PropertyType.HOUSE))
