"""Scraper service — Task runner.

Required functions: store_result(task_id, payload, extracted, score)
                    insert_lead(extracted_json)
"""
from app.services.ai_scraper.task_runner import store_result, insert_lead

__all__ = ["store_result", "insert_lead"]
