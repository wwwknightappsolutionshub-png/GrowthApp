"""Scraper service — HTML parser / content extractor."""
from app.services.ai_scraper.parser import generate_initial_urls

parse_content = generate_initial_urls  # alias for spec-required name

__all__ = ["parse_content"]
