"""Super Admin — AI Lead Intelligence Engine.

GET  /api/admin/ai_engine/prompt         — read-only extraction prompt
GET  /api/admin/ai_engine/scoring        — scoring engine config
PUT  /api/admin/ai_engine/scoring        — update scoring weights
GET  /api/admin/ai_engine/dedupe         — duplicate suppression rules
PUT  /api/admin/ai_engine/dedupe         — update dedupe config
GET  /api/admin/ai_engine/fraud          — fraud/spam rules
PUT  /api/admin/ai_engine/fraud          — update fraud rules
POST /api/admin/ai_engine/test-score     — score a sample lead
POST /api/admin/ai_engine/test-dedupe    — test dedupe on a lead
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import SuperAdmin

router = APIRouter(prefix="/api/admin/ai_engine", tags=["Admin — AI Engine"])

# In-memory config store (persisted via DB in full deployment)
_scoring_config: dict[str, Any] = {
    "phone_points": 20,
    "email_points": 20,
    "service_need_points": 15,
    "location_points": 15,
    "urgency_points": 10,
    "name_points": 10,
    "intent_high_points": 10,
    "cap": 100,
}

_dedupe_config: dict[str, Any] = {
    "enabled": True,
    "window_days": 30,
    "fields": ["email", "phone"],
    "similarity_threshold": 0.85,
}

_fraud_config: dict[str, Any] = {
    "enabled": True,
    "block_disposable_emails": True,
    "min_score_threshold": 10,
    "block_keywords": ["test", "dummy", "fake"],
}

_EXTRACTION_PROMPT = """You are CustomerFlow's Lead Intelligence Engine.

RULESET 1 — OUTPUT FORMAT (NO DEVIATION ALLOWED)
Output a single JSON object with fields: name, email, phone, business, location,
service_need, category, intent_level, revenue_estimate, urgency, ai_score.

RULESET 2 — EXTRACTION RULES
Extract ONLY information that exists. Never hallucinate. Empty string for missing.
Normalise UK phone numbers to E.164. Real names only. Clear service_need.
intent_level: low | medium | high. urgency: immediate | soon | flexible | ""

RULESET 3 — AI SCORE (+20 phone, +20 email, +15 job, +15 location,
+10 urgency immediate/soon, +10 name/business, +10 intent high) cap 100.

RULESET 4 — VALIDATION
All keys present. Strings except ai_score (int). Valid JSON. No extra text."""


class ScoringConfig(BaseModel):
    phone_points: int
    email_points: int
    service_need_points: int
    location_points: int
    urgency_points: int
    name_points: int
    intent_high_points: int
    cap: int


class DedupeConfig(BaseModel):
    enabled: bool
    window_days: int
    fields: list[str]
    similarity_threshold: float


class FraudConfig(BaseModel):
    enabled: bool
    block_disposable_emails: bool
    min_score_threshold: int
    block_keywords: list[str]


class TestLeadPayload(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    business: str = ""
    location: str = ""
    service_need: str = ""
    intent_level: str = ""
    urgency: str = ""


@router.get("/prompt")
async def get_prompt(_: SuperAdmin):
    return {"prompt": _EXTRACTION_PROMPT, "readonly": True}


@router.get("/scoring")
async def get_scoring(_: SuperAdmin):
    return _scoring_config


@router.put("/scoring")
async def update_scoring(body: ScoringConfig, _: SuperAdmin):
    _scoring_config.update(body.model_dump())
    return _scoring_config


@router.get("/dedupe")
async def get_dedupe(_: SuperAdmin):
    return _dedupe_config


@router.put("/dedupe")
async def update_dedupe(body: DedupeConfig, _: SuperAdmin):
    _dedupe_config.update(body.model_dump())
    return _dedupe_config


@router.get("/fraud")
async def get_fraud(_: SuperAdmin):
    return _fraud_config


@router.put("/fraud")
async def update_fraud(body: FraudConfig, _: SuperAdmin):
    _fraud_config.update(body.model_dump())
    return _fraud_config


@router.post("/test-score")
async def test_score(body: TestLeadPayload, _: SuperAdmin):
    from app.services.ai.scoring_engine import compute_score
    fields = body.model_dump()
    score = compute_score(fields, _scoring_config)
    return {"fields": fields, "ai_score": score}


@router.post("/test-dedupe")
async def test_dedupe(body: TestLeadPayload, _: SuperAdmin, db: AsyncSession = Depends(get_db)):
    from app.services.ai.dedupe_engine import is_duplicate
    is_dup = await is_duplicate(db, body.model_dump(), _dedupe_config)
    return {"is_duplicate": is_dup}
