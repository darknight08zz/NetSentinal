from pydantic import BaseModel
from datetime import datetime

class ModelRun(BaseModel):
    run_id: str
    model_name: str
    trained_at: datetime
    dataset: str
    hyperparams: dict
    metrics: dict
    model_path: str
