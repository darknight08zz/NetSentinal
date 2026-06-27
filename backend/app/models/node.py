from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class Node(BaseModel):
    ip: str
    first_seen: datetime
    last_seen: datetime
    total_flows: int = 0
    total_alerts: int = 0
    risk_score: float = 0.0
    role: Literal["internal", "external"]
