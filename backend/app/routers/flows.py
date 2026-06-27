from fastapi import APIRouter
from backend.app.ml.explainer import explain_flow
from backend.app.config import MODEL_ARTIFACTS_DIR
import joblib
import json
import torch
import os
from backend.app.ml.autoencoder import Autoencoder

router = APIRouter(prefix="/api/flow", tags=["flows"])

@router.get("/{flow_id}/explain")
async def get_flow_explanation(flow_id: str):
    from backend.app.db import get_db
    db = get_db()
    flow_data = await db.flows.find_one({"flow_id": flow_id})
    if not flow_data:
        return {"error": "Flow not found"}
        
    try:
        scaler = joblib.load(os.path.join(MODEL_ARTIFACTS_DIR, "scaler.joblib"))
        if_model = joblib.load(os.path.join(MODEL_ARTIFACTS_DIR, "isolation_forest.joblib"))
        triage_model = joblib.load(os.path.join(MODEL_ARTIFACTS_DIR, "triage_rf.joblib"))
        
        with open(os.path.join(MODEL_ARTIFACTS_DIR, "fusion_config.json")) as f:
            fusion_config = json.load(f)
            
        feature_cols = fusion_config["feature_cols"]
        input_dim = len(feature_cols)
        
        ae_model = Autoencoder(input_dim)
        ae_model.load_state_dict(torch.load(os.path.join(MODEL_ARTIFACTS_DIR, "autoencoder.pt")))
        
        features = flow_data.get("features", {})
        explanation = explain_flow(
            flow_features=features,
            scaler=scaler,
            if_model=if_model,
            ae_model=ae_model,
            triage_model=triage_model,
            fusion_stats=fusion_config["stats"],
            threshold=fusion_config["threshold"],
            feature_names=feature_cols
        )
        return explanation
    except Exception as e:
        return {"error": f"Failed to generate explanation: {str(e)}"}
