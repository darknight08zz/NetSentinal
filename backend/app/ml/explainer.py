import numpy as np
import torch

def explain_flow(flow_features: dict, scaler, if_model, ae_model, triage_model, fusion_stats: dict, threshold: float, feature_names: list[str]) -> dict:
    """
    Given one flow's raw feature dict, traces it through the ML pipeline to produce
    a step-by-step explainable payload.
    """
    # 1. Raw to Normalized
    # Ensure order matches feature_names
    raw_array = np.array([[flow_features.get(f, 0.0) for f in feature_names]])
    norm_array = scaler.transform(raw_array)
    
    # 2. Autoencoder Latent & Reconstruction
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ae_model.eval()
    ae_model.to(device)
    
    x_tensor = torch.tensor(norm_array, dtype=torch.float32).to(device)
    with torch.no_grad():
        latent_tensor = ae_model.encoder(x_tensor)
        recon_tensor = ae_model.decoder(latent_tensor)
        
        latent = latent_tensor.cpu().numpy()[0].tolist()
        recon = recon_tensor.cpu().numpy()[0].tolist()
        
        # Per feature MSE
        per_feature_error = ((x_tensor - recon_tensor) ** 2).cpu().numpy()[0]
        ae_error = float(np.mean(per_feature_error))
    
    # Identify top 5 contributing features to the error
    error_dict = {feat: float(err) for feat, err in zip(feature_names, per_feature_error)}
    top_contributors = sorted(error_dict.keys(), key=lambda k: error_dict[k], reverse=True)[:5]
    
    # 3. Isolation Forest
    # raw decision function
    if_raw = float(-if_model.decision_function(norm_array)[0])
    
    # simplified representation of depth (inverse to score)
    # The more anomalous, the shorter the path
    avg_depth = 15.0 - (if_raw * 5.0) # heuristic for visualization purposes
    
    # 4. Fusion
    if_std = fusion_stats["if_std"] if fusion_stats["if_std"] > 0 else 1e-6
    if_norm = (if_raw - fusion_stats["if_mean"]) / if_std
    
    ae_std = fusion_stats["ae_std"] if fusion_stats["ae_std"] > 0 else 1e-6
    ae_norm = (ae_error - fusion_stats["ae_mean"]) / ae_std
    
    fused_score = float((if_norm * 0.5) + (ae_norm * 0.5))
    
    # 5. Verdict and Triage
    is_anomalous = fused_score > threshold
    verdict = "ANOMALOUS" if is_anomalous else "BENIGN"
    
    pred_attack = None
    confidence = None
    
    if is_anomalous:
        preds = triage_model.predict(norm_array)
        probs = triage_model.predict_proba(norm_array)
        pred_attack = str(preds[0])
        confidence = float(np.max(probs[0]))
    
    return {
        "raw_features": {f: float(raw_array[0][i]) for i, f in enumerate(feature_names)},
        "normalized_features": {f: float(norm_array[0][i]) for i, f in enumerate(feature_names)},
        "autoencoder_latent": latent,
        "reconstruction": {f: float(recon[i]) for i, f in enumerate(feature_names)},
        "per_feature_error": error_dict,
        "top_contributing_features": top_contributors,
        "isolation_forest_avg_depth": max(1.0, float(avg_depth)),
        "if_score": if_raw,
        "ae_error": ae_error,
        "fused_score": fused_score,
        "threshold": threshold,
        "verdict": verdict,
        "predicted_attack_type": pred_attack,
        "confidence": confidence
    }
