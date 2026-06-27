from fastapi import APIRouter, Query
from typing import Optional
from backend.app.db import get_db
from pydantic import BaseModel

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

class StatusUpdate(BaseModel):
    status: str

@router.get("")
async def get_alerts(severity: Optional[str] = None, status: Optional[str] = None, since: Optional[str] = None, limit: int = Query(50, le=1000)):
    db = get_db()
    query = {}
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status
    
    cursor = db.alerts.find(query).sort("timestamp", -1).limit(limit)
    alerts = []
    async for document in cursor:
        document["_id"] = str(document["_id"])
        alerts.append(document)
    return alerts

@router.get("/{alert_id}")
async def get_alert(alert_id: str):
    db = get_db()
    from bson import ObjectId
    alert = await db.alerts.find_one({"_id": ObjectId(alert_id)})
    if alert:
        alert["_id"] = str(alert["_id"])
        return alert
    return {"error": "Alert not found"}

@router.patch("/{alert_id}")
async def update_alert_status(alert_id: str, update: StatusUpdate):
    db = get_db()
    from bson import ObjectId
    result = await db.alerts.update_one(
        {"_id": ObjectId(alert_id)},
        {"$set": {"status": update.status}}
    )
    return {"updated": result.modified_count > 0}
