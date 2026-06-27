from pydantic import BaseModel
from datetime import datetime
from typing import Literal, Optional

class Alert(BaseModel):
    flow_id: str
    timestamp: datetime
    if_score: float
    ae_error: float
    fused_score: float
    severity: Literal["low", "medium", "high", "critical"]
    predicted_attack_type: Optional[str] = None
    confidence: Optional[float] = None
    status: Literal["new", "reviewed", "confirmed", "false_positive"] = "new"
    src_ip: str
    dst_ip: str
