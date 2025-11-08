from pydantic import BaseModel
from typing import List, Dict, Any

class CheckRequest(BaseModel):
    new_drug: str
    current: List[str]

class Alert(BaseModel):
    pair: List[str]
    severity: str
    description: str
    management: str
    sources: List[Dict[str, str]]
    proof: Dict[str, Any]
