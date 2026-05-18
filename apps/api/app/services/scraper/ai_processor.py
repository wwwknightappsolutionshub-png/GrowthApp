"""Scraper service — AI batch processor.

Required function: process_batch(batch_content)
"""
from app.services.ai_scraper.ai_processor import process_batch

__all__ = ["process_batch"]
