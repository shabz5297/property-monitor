"""
Tests for the config-driven HTML scraper, run entirely against a local
fixture file -- no network, no dependency on any real site's structure
or availability.
"""
from pathlib import Path

from property_monitor.models import PropertyType
from property_monitor.sources.html_source import SiteConfig, parse_listing_page

FIXTURE = (Path(__file__).parent / "fixtures" / "sample_agent_listings.html").read_text()

CONFIG = SiteConfig(
    source_name="sample-agent",
    base_url="https://sample-agent.example.invalid",
    card_selector=".property-card",
    title_selector=".property-card__title",
    price_selector=".property-card__price",
    location_selector=".property-card__location",
    url_selector=".property-card__link",
    id_attribute="data-listing-id",
)


def test_parses_all_complete_cards():
    listings = parse_listing_page(FIXTURE, CONFIG)
    # 5 cards in the fixture, 1 is deliberately incomplete (no price) -> 4 expected
    assert len(listings) == 4


def test_skips_incomplete_card():
    listings = parse_listing_page(FIXTURE, CONFIG)
    ids = {p.source_id for p in listings}
    assert "A104" not in ids  # the "Coming Soon" card with no price


def test_extracts_price_and_bedrooms_correctly():
    listings = parse_listing_page(FIXTURE, CONFIG)
    a101 = next(p for p in listings if p.source_id == "A101")
    assert a101.price_gbp == 285_000
    assert a101.bedrooms == 3
    assert a101.location == "Sturry Road, Canterbury"


def test_resolves_relative_url_against_base_url():
    listings = parse_listing_page(FIXTURE, CONFIG)
    a101 = next(p for p in listings if p.source_id == "A101")
    assert a101.url == "https://sample-agent.example.invalid/property/a101-sturry-road"


def test_guesses_property_type_from_title():
    listings = parse_listing_page(FIXTURE, CONFIG)
    by_id = {p.source_id: p for p in listings}
    assert by_id["A101"].property_type == PropertyType.HOUSE       # "Semi-Detached House"
    assert by_id["A102"].property_type == PropertyType.FLAT        # "Apartment"
    assert by_id["A103"].property_type == PropertyType.HOUSE       # "Detached"
    assert by_id["A105"].property_type == PropertyType.LAND        # "Building Plot"


def test_uses_id_attribute_not_url_when_available():
    listings = parse_listing_page(FIXTURE, CONFIG)
    a101 = next(p for p in listings if p.title.startswith("3 Bedroom"))
    assert a101.source_id == "A101"
    assert a101.listing_id == "sample-agent:A101"


def test_falls_back_to_url_as_id_when_no_id_attribute_configured():
    config_no_id = SiteConfig(
        source_name="sample-agent",
        base_url="https://sample-agent.example.invalid",
        card_selector=".property-card",
        title_selector=".property-card__title",
        price_selector=".property-card__price",
        location_selector=".property-card__location",
        url_selector=".property-card__link",
        # id_attribute intentionally omitted
    )
    listings = parse_listing_page(FIXTURE, config_no_id)
    a101 = next(p for p in listings if p.title.startswith("3 Bedroom"))
    assert a101.source_id == a101.url
