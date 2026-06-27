import numpy as np
from sklearn.ensemble import RandomForestClassifier

def train_triage_classifier(X_train_attack: np.ndarray, y_train_attack: np.ndarray, n_estimators: int = 50, random_state: int = 42) -> RandomForestClassifier:
    """
    Trains a Random Forest classifier to predict the specific attack type.
    This is trained ONLY on anomalous (attack) traffic.
    """
    print(f"Training Triage Classifier on {len(X_train_attack)} attack samples...")
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state, n_jobs=-1, class_weight='balanced')
    model.fit(X_train_attack, y_train_attack)
    return model

def predict_attack(model: RandomForestClassifier, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Returns the predicted attack types and the confidence (probability) of the prediction.
    """
    preds = model.predict(X)
    probs = model.predict_proba(X)
    confidences = np.max(probs, axis=1)
    return preds, confidences
