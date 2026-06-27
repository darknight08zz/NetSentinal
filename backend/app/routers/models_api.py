from fastapi import APIRouter, BackgroundTasks
import os
import json
from backend.app.config import MODEL_ARTIFACTS_DIR
import subprocess

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("")
async def list_models():
    metrics_path = os.path.join(MODEL_ARTIFACTS_DIR, "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            metrics = json.load(f)
        return {"run_id": "latest", "metrics": metrics}
    return {"error": "No trained models found"}

def train_background():
    subprocess.run(["python", "backend/app/ml/train.py"])

@router.post("/train")
async def train_models(background_tasks: BackgroundTasks):
    background_tasks.add_task(train_background)
    return {"status": "Training job started", "run_id": "new_run"}
