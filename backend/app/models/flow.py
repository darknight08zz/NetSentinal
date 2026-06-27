from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal

class Flow(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    flow_id: str
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    duration_ms: float
    features: dict[str, float]
    source: Literal["cicids2017", "nsl_kdd", "pcap_replay", "live"]
    scored: bool = False
