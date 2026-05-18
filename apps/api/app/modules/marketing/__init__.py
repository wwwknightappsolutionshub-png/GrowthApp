"""Marketing CMS module.

Powers the public website (hero, stats, platform pillars, industries, pricing,
testimonials, faq) and the visitor review-capture pipeline.

Everything is platform-wide (not per-tenant) and gated by super-admin for
writes. Reads are public.
"""
