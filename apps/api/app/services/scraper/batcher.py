"""Scraper service — Content batcher."""
from app.services.ai_scraper.batcher import batch_content

build_batches = batch_content  # alias for spec-required name

__all__ = ["build_batches"]
