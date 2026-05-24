"""Validate tenant Google credential registration payloads."""
from __future__ import annotations

from pydantic import BaseModel, Field


class GoogleCredentialsRegister(BaseModel):
    google_client_id: str = Field(min_length=10, max_length=512)
    google_client_secret: str = Field(min_length=10, max_length=512)
