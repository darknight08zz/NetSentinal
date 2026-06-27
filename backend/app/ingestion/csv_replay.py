import os
import time
import asyncio
import uuid
import json
import random
import pandas as pd
import numpy as np
import torch
import joblib
from datetime import datetime, timezone
from pymongo import UpdateOne
from backend.app.config import MODEL_ARTIFACTS_DIR
from backend.app.ml.autoencoder import Autoencoder
from backend.app.ws.manager import manager

# Simulated IPs for demo purposes since the pre-cleaned dataset doesn't include them
INTERNAL_IPS = [f"10.0.0.{i}" for i in range(1, 21)]
EXTERNAL_IPS = [f"203.0.113.{i}" for i in range(1, 51)]

async def replay_csv_stream(dataset: str, rate_per_sec: int, active_state: dict):
    from backend.app.db import get_db
    db = get_db()
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PROJECT_ROOT = os.path.dirname(BASE_DIR)
    
    test_path = os.path.join(PROJECT_ROOT, "data", "processed", "test.parquet")
    if not os.path.exists(test_path):
        print(f"Test data not found at {test_path}")
        active_state["is_running"] = False
        return
        
    print("Loading models for replay...")
    scaler = joblib.load(os.path.join(MODEL_ARTIFACTS_DIR, "scaler.joblib"))
    if_model = joblib.load(os.path.join(MODEL_ARTIFACTS_DIR, "isolation_forest.joblib"))
    triage_model = joblib.load(os.path.join(MODEL_ARTIFACTS_DIR, "triage_rf.joblib"))
    
    with open(os.path.join(MODEL_ARTIFACTS_DIR, "fusion_config.json")) as f:
        fusion_config = json.load(f)
        
    feature_cols = fusion_config["feature_cols"]
    input_dim = len(feature_cols)
    
    ae_model = Autoencoder(input_dim)
    ae_model.load_state_dict(torch.load(os.path.join(MODEL_ARTIFACTS_DIR, "autoencoder.pt")))
    
    print("Loading test data into memory...")
    df = pd.read_parquet(test_path)
    X = df[feature_cols].values
    
    batch_size = rate_per_sec
    total_rows = len(X)
    
    async def update_nodes(src_ip, dst_ip, is_alert, risk_score):
        for ip, role in [(src_ip, "internal"), (dst_ip, "external")]:
            await db.nodes.update_one(
                {"ip": ip},
                {
                    "$set": {"role": role, "last_seen": datetime.now(timezone.utc)},
                    "$setOnInsert": {"first_seen": datetime.now(timezone.utc)},
                    "$inc": {"total_flows": 1, "total_alerts": 1 if is_alert else 0},
                    "$max": {"risk_score": risk_score}
                },
                upsert=True
            )
    
    print(f"Starting replay at {rate_per_sec} flows/sec...")
    idx = 0
    while active_state["is_running"] and idx < total_rows:
        start_time = time.time()
        
        end_idx = min(idx + batch_size, total_rows)
        batch_X = X[idx:end_idx]
        
        batch_X_scaled = scaler.transform(batch_X)
        if_scores = -if_model.decision_function(batch_X_scaled)
        
        ae_model.eval()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        ae_model.to(device)
        with torch.no_grad():
            x_tensor = torch.tensor(batch_X_scaled, dtype=torch.float32).to(device)
            recon = ae_model(x_tensor)
            ae_errors = ((x_tensor - recon) ** 2).mean(dim=1).cpu().numpy()
            
        stats = fusion_config["stats"]
        if_std = stats["if_std"] if stats["if_std"] > 0 else 1e-6
        if_norm = (if_scores - stats["if_mean"]) / if_std
        ae_std = stats["ae_std"] if stats["ae_std"] > 0 else 1e-6
        ae_norm = (ae_errors - stats["ae_mean"]) / ae_std
        fused_scores = (if_norm * 0.5) + (ae_norm * 0.5)
        
        threshold = fusion_config["threshold"]
        
        flow_docs = []
        alert_docs = []
        
        for i in range(len(batch_X)):
            is_anomalous = fused_scores[i] > threshold
            
            src_ip = random.choice(INTERNAL_IPS)
            dst_ip = random.choice(EXTERNAL_IPS)
            flow_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            feature_dict = {feat: float(batch_X[i][j]) for j, feat in enumerate(feature_cols)}
            
            flow_doc = {
                "flow_id": flow_id,
                "timestamp": now,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": random.randint(1024, 65535),
                "dst_port": random.choice([80, 443, 22, 53]),
                "protocol": "TCP",
                "duration_ms": feature_dict.get("Flow Duration", 0.0),
                "features": feature_dict,
                "source": "pcap_replay",
                "scored": True
            }
            flow_docs.append(flow_doc)
            
            if is_anomalous:
                preds = triage_model.predict([batch_X_scaled[i]])
                probs = triage_model.predict_proba([batch_X_scaled[i]])
                pred_attack = str(preds[0])
                confidence = float(np.max(probs[0]))
                
                margin = fused_scores[i] - threshold
                if margin > 3.0: severity = "critical"
                elif margin > 1.5: severity = "high"
                elif margin > 0.5: severity = "medium"
                else: severity = "low"
                
                alert_doc = {
                    "flow_id": flow_id,
                    "timestamp": now,
                    "if_score": float(if_scores[i]),
                    "ae_error": float(ae_errors[i]),
                    "fused_score": float(fused_scores[i]),
                    "severity": severity,
                    "predicted_attack_type": pred_attack,
                    "confidence": confidence,
                    "status": "new",
                    "src_ip": src_ip,
                    "dst_ip": dst_ip
                }
                alert_docs.append(alert_doc)
                
                ws_alert = alert_doc.copy()
                ws_alert["timestamp"] = ws_alert["timestamp"].isoformat()
                asyncio.create_task(manager.broadcast({"type": "alert", "data": ws_alert}))
                
            await update_nodes(src_ip, dst_ip, is_anomalous, float(fused_scores[i]))
            
        if flow_docs:
            await db.flows.insert_many(flow_docs)
        if alert_docs:
            await db.alerts.insert_many(alert_docs)
            
        asyncio.create_task(manager.broadcast({"type": "topology_update", "data": {}}))
        
        idx += batch_size
        elapsed = time.time() - start_time
        sleep_time = max(0.0, 1.0 - elapsed)
        await asyncio.sleep(sleep_time)

    active_state["is_running"] = False
    print("Replay stream finished or stopped.")
