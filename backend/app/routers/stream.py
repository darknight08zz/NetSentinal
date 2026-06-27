from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
import asyncio

router = APIRouter(prefix="/api/stream", tags=["stream"])

class StreamReq(BaseModel):
    dataset: str = "cicids2017"
    rate_per_sec: int = 50

# Global active stream task control
active_stream = {"is_running": False}

@router.post("/start")
async def start_stream(req: StreamReq, background_tasks: BackgroundTasks):
    from backend.app.ingestion.csv_replay import replay_csv_stream
    if active_stream["is_running"]:
        return {"status": "Stream already running"}
    active_stream["is_running"] = True
    background_tasks.add_task(replay_csv_stream, req.dataset, req.rate_per_sec, active_stream)
    return {"status": "Stream started"}

@router.post("/stop")
async def stop_stream():
    active_stream["is_running"] = False
    return {"status": "Stream stopped"}
