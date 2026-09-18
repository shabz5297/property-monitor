"""
A generic scraper for individual estate-agent listing pages.

Instead of writing a bespoke scraper class per site, each site gets a
small SiteConfig describing where things live in its HTML (CSS
selectors). HTMLListingSource does the actual fetch + parse using that
config. Adding a new site is "write a config", not "write a scraper".

IMPORTANT: this only fetches and parses. Before pointing it at a real
site, check property_monitor/utils/robots.py against that site's
robots.txt, and read its Terms of Use yourself. Different independent
agent sites will differ -- there's no blanket answer here.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .models import Property, PropertyType
from .sources.base import PropertySource
from .utils.robots import DEFAULT_USER_AGENT, can_fetch

_PRICE_RE = re.compile(r"[\d,]+")
_BEDROOM_RE = re.compile(r"(\d+)\s*bed", re.IGNORECASE)

_TYPE_KEYWORDS = {
    PropertyType.FLAT: ("flat", "apartment", "maisonette"),
    PropertyType.BUNGALOW: ("bungalow",),
    PropertyType.LAND: ("land", "plot"),
    PropertyType.HOUSE: ("house", "detached", "semi-detached", "terraced", "cottage"),
}


def _parse_price(text: str) -> Optional[int]:
    match = _PRICE_RE.search(text or "")
    if not match:
        return None
    return int(match.group(0).replace(",", ""))


def _parse_bedrooms(text: str) -> Optional[int]:
    match = _BEDROOM_RE.search(text or "")
    return int(match.group(1)) if match else None


def _guess_property_type(text: str) -> PropertyType:
    lowered = (text or "").lower()
    for ptype, keywords in _TYPE_KEYWORDS.items():
        if any(k in lowered for k in keywords):
            return ptype
    return PropertyType.OTHER


@dataclass(frozen=True)
class SiteConfig:
    """CSS selectors describing one agent site's listing page.

    Selectors are relative to each `card_selector` match, except
    `card_selector` itself, which is relative to the whole page.
    """

    source_name: str          # short slug, e.g. "acme-agents"
    base_url: str             # used to resolve relative links
    card_selector: str        # one element per listing card
    title_selector: str
    price_selector: str
    location_selector: str
    url_selector: str         # the <a> tag whose href is the listing link
    bedrooms_selector: Optional[str] = None  # falls back to parsing title/card text
    id_attribute: Optional[str] = None       # e.g. "data-listing-id"; falls back to URL


def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


def parse_listing_page(html: str, config: SiteConfig) -> list[Property]:
    """Pure parsing function -- no network -- so it's unit-testable."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[Property] = []

    for card in soup.select(config.card_selector):
        title_el = card.select_one(config.title_selector)
        price_el = card.select_one(config.price_selector)
        location_el = card.select_one(config.location_selector)
        link_el = card.select_one(config.url_selector)

        title = _text(title_el)
        price = _parse_price(_text(price_el))
        location = _text(location_el)
        href = link_el.get("href") if link_el else None

        if not (title and price is not None and location and href):
            # Incomplete card -- skip rather than guess at missing data.
            continue

        url = urljoin(config.base_url, href)

        if config.bedrooms_selector:
            bedrooms = _parse_bedrooms(_text(card.select_one(config.bedrooms_selector)))
        else:
            bedrooms = _parse_bedrooms(title) or _parse_bedrooms(card.get_text(" "))

        if config.id_attribute and card.has_attr(config.id_attribute):
            source_id = card[config.id_attribute]
        else:
            source_id = url  # the URL itself is a perfectly good stable ID

        results.append(
            Property(
                source_name=config.source_name,
                source_id=str(source_id),
                title=title,
                price_gbp=price,
                location=location,
                bedrooms=bedrooms,
                property_type=_guess_property_type(f"{title} {card.get_text(' ')}"),
                url=url,
            )
        )

    return results


class HTMLListingSource(PropertySource):
    """Fetches a listing page over HTTP and parses it with SiteConfig."""

    def __init__(self, config: SiteConfig, listings_url: str, polite_delay: float = 1.0):
        self.name = config.source_name
        self.config = config
        self.listings_url = listings_url
        self.polite_delay = polite_delay
        self._session = requests.Session()
        self._session.headers["User-Agent"] = DEFAULT_USER_AGENT

    def fetch_listings(self, location: str) -> Iterable[Property]:
        if not can_fetch(self.listings_url):
            raise PermissionError(
                f"robots.txt for {self.listings_url} does not permit fetching this URL. "
                "Check the site's robots.txt and Terms of Use before scraping it."
            )

        time.sleep(self.polite_delay)  # be a polite crawler
        response = self._session.get(self.listings_url, timeout=15)
        response.raise_for_status()

        listings = parse_listing_page(response.text, self.config)
        # location isn't always a query param on small sites -- filter client-side
        return [p for p in listings if location.lower() in p.location.lower()]
