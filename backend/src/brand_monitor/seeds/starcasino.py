"""StarCasino brand seed — bootstraps a fresh DB.

Production sources brand config from the DB; the seed lives in code so the
classifier has something to work with offline (tests, CI, fresh installs).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrandSeed:
    slug: str
    name: str
    geo: str
    official_domains: frozenset[str] = field(default_factory=frozenset)
    known_partners: frozenset[str] = field(default_factory=frozenset)
    known_competitors: frozenset[str] = field(default_factory=frozenset)
    monitored_keywords: tuple[str, ...] = ()

    @classmethod
    def from_db_row(cls, brand: object, monitored_keywords: tuple[str, ...] = ()) -> "BrandSeed":
        """Hydrate a frozen seed from a live ``Brand`` ORM row.

        Whitelist mutations from the admin endpoints become visible to the
        classifier on the next scan without an app restart.
        """
        return cls(
            slug=getattr(brand, "slug"),
            name=getattr(brand, "name"),
            geo=getattr(brand, "geo"),
            official_domains=frozenset(getattr(brand, "official_domains") or ()),
            known_partners=frozenset(getattr(brand, "known_partners") or ()),
            known_competitors=frozenset(getattr(brand, "known_competitors") or ()),
            monitored_keywords=monitored_keywords,
        )


STARCASINO = BrandSeed(
    slug="starcasino",
    name="StarCasino",
    geo="NL",
    official_domains=frozenset(
        {
            "starcasino.nl",
            "starcasino.be",
            "starcasino.com",
            # Star Group family — same operator (Star Group SA) owns these
            # umbrella / vertical domains. Without them the classifier
            # mislabels star.be as informational despite it being the
            # group's parent landing page.
            "star.be",
            "stars.be",
            "starsport.be",
            "stardice.be",
        }
    ),
    # Bootstrap-only — production grows the list via the manual review queue.
    known_partners=frozenset(
        {
            "casino.nl",
            "onlinecasinoground.nl",
            "casinoscout.nl",
        }
    ),
    known_competitors=frozenset(
        {
            "hollandcasino.nl",
            "jackscasino.nl",
            "betcity.nl",
            "tombola.nl",
            "fairplaycasino.nl",
            "krooncasino.com",
            "unibet.nl",
            "bet365.com",
            "leovegas.com",
        }
    ),
    monitored_keywords=("starcasino", "starcasino bonus", "starcasino review"),
)


BRANDS: dict[str, BrandSeed] = {STARCASINO.slug: STARCASINO}
