"""
Check whether a site's robots.txt permits fetching a given URL, before
you ever point a scraper at it.

This is a check, not a guarantee: robots.txt only covers automated
crawling, not a site's full Terms of Use, and some sites have no
robots.txt at all (which this treats as "allowed" per the standard,
but you should still sanity-check the actual Terms page yourself).

Usage:
    python3 -m property_monitor.utils.robots https://example-agent.co.uk/listings
"""
from __future__ import annotations

import sys
import urllib.robotparser
from urllib.parse import urlparse

DEFAULT_USER_AGENT = "PropertyMonitorBot/0.1 (+contact: you@example.com)"


def can_fetch(url: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
    """Return True if robots.txt for the URL's host allows fetching it."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as exc:  # noqa: BLE001
        print(f"Could not read {robots_url}: {exc}. Treat as NOT permitted until checked manually.")
        return False

    return rp.can_fetch(user_agent, url)


def crawl_delay(url: str, user_agent: str = DEFAULT_USER_AGENT) -> float | None:
    """Return the site's requested crawl-delay in seconds, if any."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:  # noqa: BLE001
        return None
    return rp.crawl_delay(user_agent)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 -m property_monitor.utils.robots <url>")
        sys.exit(1)

    target = sys.argv[1]
    allowed = can_fetch(target)
    delay = crawl_delay(target)

    print(f"URL:          {target}")
    print(f"robots.txt allows fetch: {allowed}")
    print(f"Requested crawl-delay:   {delay if delay is not None else 'none specified'}")
    print(
        "\nNote: this only checks robots.txt. Also read the site's actual "
        "Terms of Use / Terms of Service page yourself before scraping it."
    )
