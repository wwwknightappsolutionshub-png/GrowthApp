"""AI Scraper module (super-admin only).

Sources, categories, tasks, results — plus a background worker that fetches
from each source's url_pattern, runs the AI extraction service, scores the
lead, inserts into the leads table, and records the result.
"""
