from fastapi import APIRouter
from backend.app.db import get_db

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("/summary")
async def get_stats_summary():
    db = get_db()
    active_alerts = await db.alerts.count_documents({"status": "new"})
    
    # Top attack type
    pipeline = [
        {"$match": {"predicted_attack_type": {"$ne": None}}},
        {"$group": {"_id": "$predicted_attack_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    cursor = db.alerts.aggregate(pipeline)
    top_attack = "None"
    async for doc in cursor:
        top_attack = doc["_id"]
        
    severity_counts = {}
    for sev in ["low", "medium", "high", "critical"]:
        severity_counts[sev] = await db.alerts.count_documents({"severity": sev})
        
    return {
        "flows_per_sec": 0, # Updated by stream phase
        "active_alerts": active_alerts,
        "top_attack_type": top_attack,
        "model_status": "Healthy",
        "severity_counts": severity_counts
    }
