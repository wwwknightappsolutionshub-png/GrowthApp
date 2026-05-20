"""Default lead source URLs per trade — seeded into ai_scraper_sources + lead_categories.

Super admin can add more via AI Scraper UI. URLs may use placeholders:
  {page}, {query}, {category}, {postcode}
"""
from __future__ import annotations

from typing import TypedDict


class CatalogSource(TypedDict):
    name: str
    url_pattern: str
    scraping_type: str
    source_platform: str
    notes: str | None


class TradeCatalog(TypedDict):
    scraper_category: str
    marketplace_category: str
    sources: list[CatalogSource]


# UK-focused directories, search engines, and review/listing platforms
CATALOG: list[TradeCatalog] = [
    {
        "scraper_category": "Plumber",
        "marketplace_category": "Plumber",
        "sources": [
            {
                "name": "Yell — Plumbers UK",
                "url_pattern": "https://www.yell.com/s/plumbers.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": "National plumber directory (paginated).",
            },
            {
                "name": "Checkatrade — Plumbers",
                "url_pattern": "https://www.checkatrade.com/Search/Plumber?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — emergency plumber",
                "url_pattern": "https://www.google.com/search?q=emergency+plumber+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": "Use with {postcode} from source geo settings.",
            },
            {
                "name": "Bing — local plumbers",
                "url_pattern": "https://www.bing.com/search?q=plumbers+near+{postcode}&first={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
            {
                "name": "Trustpilot — plumbing companies",
                "url_pattern": "https://www.trustpilot.com/search?query=plumber",
                "scraping_type": "html",
                "source_platform": "review_site",
                "notes": "Review/listing discovery.",
            },
        ],
    },
    {
        "scraper_category": "Electrician",
        "marketplace_category": "Electrician",
        "sources": [
            {
                "name": "Yell — Electricians",
                "url_pattern": "https://www.yell.com/s/electricians.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Checkatrade — Electricians",
                "url_pattern": "https://www.checkatrade.com/Search/Electrician?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — electrician",
                "url_pattern": "https://www.google.com/search?q=electrician+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
            {
                "name": "NICEIC find a contractor",
                "url_pattern": "https://www.niceic.com/contractor-search",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": "Trade body directory.",
            },
        ],
    },
    {
        "scraper_category": "Cleaner",
        "marketplace_category": "Cleaner",
        "sources": [
            {
                "name": "Yell — Cleaners",
                "url_pattern": "https://www.yell.com/s/cleaners.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — cleaning services",
                "url_pattern": "https://www.google.com/search?q=domestic+cleaning+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
            {
                "name": "Bark — cleaners",
                "url_pattern": "https://www.bark.com/en/gb/cleaners/",
                "scraping_type": "marketplace",
                "source_platform": "marketplace",
                "notes": "Lead marketplace style listings.",
            },
        ],
    },
    {
        "scraper_category": "Roofer",
        "marketplace_category": "Roofer",
        "sources": [
            {
                "name": "Yell — Roofers",
                "url_pattern": "https://www.yell.com/s/roofers.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Checkatrade — Roofers",
                "url_pattern": "https://www.checkatrade.com/Search/Roofer?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — roofer",
                "url_pattern": "https://www.google.com/search?q=roofer+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
        ],
    },
    {
        "scraper_category": "Painter & Decorator",
        "marketplace_category": "Painter & Decorator",
        "sources": [
            {
                "name": "Yell — Painters",
                "url_pattern": "https://www.yell.com/s/painters-and-decorators.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — painter decorator",
                "url_pattern": "https://www.google.com/search?q=painter+decorator+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
        ],
    },
    {
        "scraper_category": "Builder",
        "marketplace_category": "Builder",
        "sources": [
            {
                "name": "Yell — Builders",
                "url_pattern": "https://www.yell.com/s/builders.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Checkatrade — Builders",
                "url_pattern": "https://www.checkatrade.com/Search/Builder?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — builder",
                "url_pattern": "https://www.google.com/search?q=builder+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
        ],
    },
    {
        "scraper_category": "Landscaper",
        "marketplace_category": "Landscaper",
        "sources": [
            {
                "name": "Yell — Landscapers",
                "url_pattern": "https://www.yell.com/s/landscape-gardeners.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — landscaper",
                "url_pattern": "https://www.google.com/search?q=landscaper+gardener+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
        ],
    },
    {
        "scraper_category": "Handyman",
        "marketplace_category": "Handyman",
        "sources": [
            {
                "name": "Yell — Handymen",
                "url_pattern": "https://www.yell.com/s/handymen.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — handyman",
                "url_pattern": "https://www.google.com/search?q=handyman+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
        ],
    },
    {
        "scraper_category": "Salon & Beauty",
        "marketplace_category": "Salon & Beauty",
        "sources": [
            {
                "name": "Yell — Hairdressers",
                "url_pattern": "https://www.yell.com/s/hairdressers.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — beauty salon",
                "url_pattern": "https://www.google.com/search?q=beauty+salon+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
        ],
    },
    {
        "scraper_category": "HVAC",
        "marketplace_category": "HVAC",
        "sources": [
            {
                "name": "Yell — Heating engineers",
                "url_pattern": "https://www.yell.com/s/central-heating-services.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — heating engineer",
                "url_pattern": "https://www.google.com/search?q=heating+engineer+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
        ],
    },
    {
        "scraper_category": "Locksmith",
        "marketplace_category": "Locksmith",
        "sources": [
            {
                "name": "Yell — Locksmiths",
                "url_pattern": "https://www.yell.com/s/locksmiths.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": None,
            },
            {
                "name": "Google Search — locksmith",
                "url_pattern": "https://www.google.com/search?q=locksmith+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
        ],
    },
    {
        "scraper_category": "Other trade",
        "marketplace_category": "Other trade",
        "sources": [
            {
                "name": "Yell — General business search",
                "url_pattern": "https://www.yell.com/s/{category}.html?page={page}",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": "Replace {category} at run time if needed.",
            },
            {
                "name": "Google Search — local business",
                "url_pattern": "https://www.google.com/search?q=local+business+{postcode}&start={page}",
                "scraping_type": "html",
                "source_platform": "search_engine",
                "notes": None,
            },
            {
                "name": "FreeIndex UK",
                "url_pattern": "https://www.freeindex.co.uk/",
                "scraping_type": "directory",
                "source_platform": "directory",
                "notes": "General UK directory.",
            },
        ],
    },
]

# UK territory seeds for marketplace geo matching (region_code = outward prefix examples)
UK_TERRITORY_SEEDS: list[tuple[str, str]] = [
    ("United Kingdom (nationwide)", "UK"),
    ("London — Central", "SW1"),
    ("London — West", "W1"),
    ("London — East", "E1"),
    ("London — North", "N1"),
    ("Manchester", "M1"),
    ("Birmingham", "B1"),
    ("Leeds", "LS1"),
    ("Bristol", "BS1"),
    ("Glasgow", "G1"),
    ("Edinburgh", "EH1"),
    ("Cardiff", "CF1"),
    ("Liverpool", "L1"),
    ("Sheffield", "S1"),
    ("Newcastle", "NE1"),
    ("Nottingham", "NG1"),
]
