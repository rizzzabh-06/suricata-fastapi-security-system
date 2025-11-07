from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Health(BaseModel):
    status: str

class EventMsg(BaseModel):
    type: str = "event"
    timestamp: str
    event_type: str
    src_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    proto: Optional[str] = None
    raw: dict

class AlertMsg(BaseModel):
    type: str = "alert"
    timestamp: str
    severity: str
    src_ip: str
    dest_ip: Optional[str] = None
    reason: str
    techniques: List[str] = []
    raw: Optional[dict] = None

class TopTalker(BaseModel):
    ip: str
    pps: float
    total_packets: int

class MitigationRequest(BaseModel):
    ip: str
    ttl: int = 300
    reason: str

class AuditItem(BaseModel):
    timestamp: str
    action: str
    ip: str
    reason: str
    ttl: Optional[int] = None
    actor: str = "system"
