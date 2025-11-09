# Backend/schema.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any

class CheckRequest(BaseModel):
    new_drug: str
    current: List[str]
    # new fields
    patient_name: Optional[str] = Field(None, min_length=1)
    age: Optional[int] = Field(None, ge=0, le=130)
    doctor_name: Optional[str] = None

class Alert(BaseModel):
    id: str
    pair: List[str]
    severity: str
    severity_score: float
    description: str
    management: str
    sources: List[Any]
    proof: Any

class CheckResponse(BaseModel):
    alerts: List[Alert]
    not_found: List[Any] = []
    visit_id: Optional[int] = None
