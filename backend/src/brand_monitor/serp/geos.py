"""Per-geo configuration for the SERP fetcher.

Everything that varies between countries — Google TLD, search params,
Playwright locale / timezone / consent cookie, DuckDuckGo region — lives
here. The fetcher reads from this registry instead of hardcoding NL.

Adding a new geo is a single ``GeoProfile`` entry below: no fetcher code
changes. The validator (``api/validation.py``) auto-picks up new geos
because it reads ``supported_geo_codes()``.

Notes on the values:

- ``google_hl`` is the UI language hint; the locale-default UI language
  is fine for unbranded queries but for SERP scraping the parser anchors
  on ``<h3>`` so language doesn't break results.
- ``consent_value`` is the long-form CONSENT cookie payload that
  bypasses the consent.google.com interstitial. Values follow the
  ``YES+<region>.<lang>+V14+BX`` pattern Google emits after a real
  browser accepts. The exact opaque payload doesn't matter; presence
  + ``YES+`` prefix is what skips the wall.
- ``consent_button_labels`` is the ordered list of localized button
  texts the page exposes if the cookie didn't take. The first match
  wins.
- ``ddg_region`` is the ``kl`` query param for ``html.duckduckgo.com``.
  See https://duckduckgo.com/duckduckgo-help-pages/settings/params/.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class GeoProfile:
    code: str
    name: str
    google_tld: str
    google_hl: str
    google_gl: str
    locale: str
    timezone: str
    accept_language: str
    consent_value: str
    socs_value: str | None
    consent_button_labels: tuple[str, ...]
    ddg_region: str


_PROFILES: dict[str, GeoProfile] = {
    "NL": GeoProfile(
        code="NL",
        name="Netherlands",
        google_tld="nl",
        google_hl="nl",
        google_gl="NL",
        locale="nl-NL",
        timezone="Europe/Amsterdam",
        accept_language="nl-NL,nl;q=0.9,en-US;q=0.7,en;q=0.5",
        consent_value="YES+NL.nl+V14+BX",
        socs_value="CAESHAgBEhJnd3NfMjAyMzAxMTAtMF9SQzIaAm5sIAEaBgiAo7CdBg",
        consent_button_labels=(
            "Alles accepteren",
            "Accept all",
            "Ik ga akkoord",
        ),
        ddg_region="nl-nl",
    ),
    "BE": GeoProfile(
        code="BE",
        name="Belgium",
        google_tld="be",
        google_hl="nl",
        google_gl="BE",
        locale="nl-BE",
        timezone="Europe/Brussels",
        accept_language="nl-BE,nl;q=0.9,fr-BE;q=0.7,fr;q=0.6,en;q=0.4",
        consent_value="YES+BE.nl+V14+BX",
        socs_value=None,
        consent_button_labels=(
            "Alles accepteren",
            "Tout accepter",
            "Accept all",
        ),
        ddg_region="be-fr",
    ),
    "DE": GeoProfile(
        code="DE",
        name="Germany",
        google_tld="de",
        google_hl="de",
        google_gl="DE",
        locale="de-DE",
        timezone="Europe/Berlin",
        accept_language="de-DE,de;q=0.9,en;q=0.6",
        consent_value="YES+DE.de+V14+BX",
        socs_value=None,
        consent_button_labels=(
            "Alle akzeptieren",
            "Accept all",
        ),
        ddg_region="de-de",
    ),
    "FR": GeoProfile(
        code="FR",
        name="France",
        google_tld="fr",
        google_hl="fr",
        google_gl="FR",
        locale="fr-FR",
        timezone="Europe/Paris",
        accept_language="fr-FR,fr;q=0.9,en;q=0.6",
        consent_value="YES+FR.fr+V14+BX",
        socs_value=None,
        consent_button_labels=(
            "Tout accepter",
            "Accept all",
        ),
        ddg_region="fr-fr",
    ),
    "GB": GeoProfile(
        code="GB",
        name="United Kingdom",
        google_tld="co.uk",
        google_hl="en",
        google_gl="GB",
        locale="en-GB",
        timezone="Europe/London",
        accept_language="en-GB,en;q=0.9",
        consent_value="YES+GB.en+V14+BX",
        socs_value=None,
        consent_button_labels=(
            "Accept all",
            "I agree",
        ),
        ddg_region="uk-en",
    ),
    "US": GeoProfile(
        code="US",
        name="United States",
        google_tld="com",
        google_hl="en",
        google_gl="US",
        locale="en-US",
        timezone="America/New_York",
        accept_language="en-US,en;q=0.9",
        consent_value="YES+US.en+V14+BX",
        socs_value=None,
        consent_button_labels=(
            "Accept all",
            "I agree",
        ),
        ddg_region="us-en",
    ),
}


def supported_geo_codes() -> list[str]:
    return sorted(_PROFILES.keys())


def get_geo_profile(geo: str) -> GeoProfile | None:
    return _PROFILES.get((geo or "").strip().upper())


def geo_profiles() -> Iterable[GeoProfile]:
    return _PROFILES.values()


# Default fallback — used by callers that pre-validated geo elsewhere
# and only want a sensible profile if the lookup somehow misses.
DEFAULT_PROFILE: GeoProfile = _PROFILES["NL"]
