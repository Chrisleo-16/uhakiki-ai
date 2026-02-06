from pydantic import BaseModel, Field
from typing import Optional, List

class OCRResult(BaseModel):
    extracted_id: Optional[str] = None
    is_academic: bool
    found_keywords: List[str]

class IngestResponse(BaseModel):
    status: str = Field(..., example="NATIONAL_RECORD_SECURED")
    risk_level: str = Field(..., example="CLEAN")
    identity_verified: bool
    forgery_score: float
    blur_score: float
    adjustment_applied: str
    evidence_url: str
    reason: Optional[str] = None