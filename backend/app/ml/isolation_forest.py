import numpy as np
from sklearn.ensemble import IsolationForest

def train_isolation_forest(X_train: np.ndarray, n_estimators: int = 200, contamination: str | float = 'auto', random_state: int = 42) -> IsolationForest:
    """
    Trains an Isolation Forest model on the full training set (unsupervised).
    """
    print(f"Training Isolation Forest with n_estimators={n_estimators}...")
    model = IsolationForest(n_estimators=n_estimators, contamination=contamination, random_state=random_state, n_jobs=-1)
    model.fit(X_train)
    return model

def score(model: IsolationForest, X: np.ndarray) -> np.ndarray:
    """
    Returns the anomaly score.
    We use decision_function. Lower values indicate anomalies.
    We invert it so that higher values indicate higher anomaly likelihood.
    """
    # decision_function returns > 0 for normal, < 0 for anomalies
    # By multiplying by -1, higher values = more anomalous.
    raw_scores = model.decision_function(X)
    return -raw_scores
