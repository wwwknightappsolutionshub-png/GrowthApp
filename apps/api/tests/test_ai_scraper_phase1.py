"""Phase 1 AI scraper helpers."""
from app.modules.ai_scraper.dedup import normalize_email, normalize_phone
from app.services.ai_scraper.extraction import _parse_extraction_json, _strip_json_fences


def test_normalize_email():
    assert normalize_email("  Admin@Example.COM ") == "admin@example.com"
    assert normalize_email("not-an-email") is None


def test_normalize_phone_uk():
    assert normalize_phone("07123 456789") == "447123456789"
    assert normalize_phone("+44 7123 456789") == "447123456789"


def test_parse_extraction_json_strips_fences():
    raw = '```json\n{"name": "Acme", "email": "", "phone": "", "business": "Acme", "location": "", "service_need": "roof", "category": "roofing", "intent_level": "high", "revenue_estimate": "", "urgency": "soon", "ai_score": 55}\n```'
    parsed = _parse_extraction_json(_strip_json_fences(raw))
    assert parsed["name"] == "Acme"
    assert parsed["ai_score"] == 55
