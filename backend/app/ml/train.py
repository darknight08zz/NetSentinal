import os
import json
import joblib
import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

from backend.app.ml.isolation_forest import train_isolation_forest, score as if_score
from backend.app.ml.autoencoder import train_autoencoder, score as ae_score
from backend.app.ml.fusion import fit_fusion_stats, fuse_scores, calculate_threshold
from backend.app.ml.triage_classifier import train_triage_classifier, predict_attack

def evaluate_binary(y_true_binary: np.ndarray, y_pred_binary: np.ndarray, fused_scores: np.ndarray) -> dict:
    cm = confusion_matrix(y_true_binary, y_pred_binary)
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    return {
        "precision": precision_score(y_true_binary, y_pred_binary, zero_division=0),
        "recall": recall_score(y_true_binary, y_pred_binary, zero_division=0),
        "f1": f1_score(y_true_binary, y_pred_binary, zero_division=0),
        "auc_roc": roc_auc_score(y_true_binary, fused_scores),
        "auc_pr": average_precision_score(y_true_binary, fused_scores),
        "fpr": fpr,
        "confusion_matrix": cm.tolist()
    }

def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    PROJECT_ROOT = os.path.dirname(BASE_DIR)
    PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
    ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    print("Loading datasets...")
    train_df = pd.read_parquet(os.path.join(PROCESSED_DIR, "train.parquet"))
    test_df = pd.read_parquet(os.path.join(PROCESSED_DIR, "test.parquet"))

    label_col = 'Attack Type' if 'Attack Type' in train_df.columns else 'Label'
    benign_label = 'Normal Traffic' if label_col == 'Attack Type' else 'BENIGN'

    feature_cols = [c for c in train_df.columns if c != label_col]

    y_train = train_df[label_col].values
    X_train = train_df[feature_cols].values

    y_test = test_df[label_col].values
    X_test = test_df[feature_cols].values

    # Separate benign flows
    train_benign_mask = (y_train == benign_label)
    X_train_benign = X_train[train_benign_mask]

    # Separate attack flows
    train_attack_mask = (y_train != benign_label)
    X_train_attack = X_train[train_attack_mask]
    y_train_attack = y_train[train_attack_mask]

    print("Scaling features...")
    scaler = StandardScaler()
    scaler.fit(X_train_benign)  # Fit only on benign to prevent data leakage of anomalies
    
    X_train_scaled = scaler.transform(X_train)
    X_train_benign_scaled = scaler.transform(X_train_benign)
    X_test_scaled = scaler.transform(X_test)
    X_train_attack_scaled = scaler.transform(X_train_attack)

    joblib.dump(scaler, os.path.join(ARTIFACTS_DIR, "scaler.joblib"))

    # 1. Train Isolation Forest
    if_model = train_isolation_forest(X_train_scaled)
    joblib.dump(if_model, os.path.join(ARTIFACTS_DIR, "isolation_forest.joblib"))

    # 2. Train Autoencoder
    input_dim = len(feature_cols)
    ae_model = train_autoencoder(X_train_benign_scaled, input_dim=input_dim, epochs=15)
    torch.save(ae_model.state_dict(), os.path.join(ARTIFACTS_DIR, "autoencoder.pt"))

    # 3. Compute Fusion Stats & Threshold
    print("Computing fusion statistics...")
    train_if_scores = if_score(if_model, X_train_scaled)
    train_ae_scores = ae_score(ae_model, X_train_scaled)

    fusion_stats = fit_fusion_stats(train_if_scores, train_ae_scores)
    train_fused = fuse_scores(train_if_scores, train_ae_scores, fusion_stats)

    benign_fused = train_fused[train_benign_mask]
    threshold = calculate_threshold(benign_fused, percentile=95.0)

    fusion_config = {
        "stats": fusion_stats,
        "threshold": threshold,
        "if_weight": 0.5,
        "percentile": 95.0,
        "feature_cols": feature_cols
    }
    with open(os.path.join(ARTIFACTS_DIR, "fusion_config.json"), "w") as f:
        json.dump(fusion_config, f, indent=4)

    # 4. Train Triage Classifier
    triage_model = train_triage_classifier(X_train_attack_scaled, y_train_attack)
    joblib.dump(triage_model, os.path.join(ARTIFACTS_DIR, "triage_rf.joblib"))

    # 5. Evaluate on Test Set
    print("Evaluating on Test Set...")
    test_if_scores = if_score(if_model, X_test_scaled)
    test_ae_scores = ae_score(ae_model, X_test_scaled)
    test_fused = fuse_scores(test_if_scores, test_ae_scores, fusion_stats)

    y_test_binary = (y_test != benign_label).astype(int)
    y_pred_binary = (test_fused > threshold).astype(int)

    binary_metrics = evaluate_binary(y_test_binary, y_pred_binary, test_fused)

    # Multi-class Triage Evaluation (Only on TRUE attacks)
    test_attack_mask = (y_test != benign_label)
    X_test_attacks_scaled = X_test_scaled[test_attack_mask]
    y_test_attacks_true = y_test[test_attack_mask]

    triage_preds, _ = predict_attack(triage_model, X_test_attacks_scaled)
    
    triage_precision = precision_score(y_test_attacks_true, triage_preds, average='macro', zero_division=0)
    triage_recall = recall_score(y_test_attacks_true, triage_preds, average='macro', zero_division=0)
    triage_f1 = f1_score(y_test_attacks_true, triage_preds, average='macro', zero_division=0)
    
    labels = np.unique(np.concatenate((y_test_attacks_true, triage_preds)))
    triage_cm = confusion_matrix(y_test_attacks_true, triage_preds, labels=labels)

    metrics_payload = {
        "binary_detection": binary_metrics,
        "triage_classification": {
            "macro_precision": triage_precision,
            "macro_recall": triage_recall,
            "macro_f1": triage_f1,
            "confusion_matrix": triage_cm.tolist(),
            "labels": labels.tolist()
        }
    }

    metrics_path = os.path.join(ARTIFACTS_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_payload, f, indent=4)

    print(f"Training complete! Metrics saved to {metrics_path}")
    print(f"Test Set Binary AUC-ROC: {binary_metrics['auc_roc']:.4f}")
    print(f"Test Set FPR: {binary_metrics['fpr']:.4f}")

if __name__ == "__main__":
    main()
