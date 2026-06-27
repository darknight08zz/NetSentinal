import numpy as np

def fit_fusion_stats(if_scores: np.ndarray, ae_scores: np.ndarray) -> dict:
    """
    Computes mean and std for Z-normalization of each model's scores.
    """
    return {
        "if_mean": float(np.mean(if_scores)),
        "if_std": float(np.std(if_scores)),
        "ae_mean": float(np.mean(ae_scores)),
        "ae_std": float(np.std(ae_scores))
    }

def fuse_scores(if_scores: np.ndarray, ae_scores: np.ndarray, stats: dict, if_weight: float = 0.5) -> np.ndarray:
    """
    Z-normalizes scores and combines them using a weighted average.
    """
    # Z-normalize Isolation Forest
    if_std = stats["if_std"] if stats["if_std"] > 0 else 1e-6
    if_norm = (if_scores - stats["if_mean"]) / if_std
    
    # Z-normalize Autoencoder
    ae_std = stats["ae_std"] if stats["ae_std"] > 0 else 1e-6
    ae_norm = (ae_scores - stats["ae_mean"]) / ae_std
    
    # Weighted average
    ae_weight = 1.0 - if_weight
    fused = (if_norm * if_weight) + (ae_norm * ae_weight)
    
    return fused

def calculate_threshold(benign_fused_scores: np.ndarray, percentile: float = 95.0) -> float:
    """
    Calculates the anomaly threshold based on the benign training set's fused scores.
    """
    threshold = np.percentile(benign_fused_scores, percentile)
    return float(threshold)
