import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

class Autoencoder(nn.Module):
    def __init__(self, input_dim: int):
        super(Autoencoder, self).__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8)  # Latent representation
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim)
        )

    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

def train_autoencoder(X_train_benign: np.ndarray, input_dim: int, epochs: int = 20, batch_size: int = 256, lr: float = 1e-3, val_split: float = 0.1) -> nn.Module:
    """
    Trains the Autoencoder on benign flows only.
    """
    print(f"Training Autoencoder for {epochs} epochs...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = Autoencoder(input_dim=input_dim).to(device)
    
    # Split into train/val
    np.random.seed(42)
    indices = np.random.permutation(len(X_train_benign))
    val_size = int(len(X_train_benign) * val_split)
    
    train_idx, val_idx = indices[val_size:], indices[:val_size]
    X_t = torch.tensor(X_train_benign[train_idx], dtype=torch.float32)
    X_v = torch.tensor(X_train_benign[val_idx], dtype=torch.float32)
    
    train_loader = DataLoader(TensorDataset(X_t, X_t), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(X_v, X_v), batch_size=batch_size, shuffle=False)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    best_val_loss = float('inf')
    best_weights = None
    patience = 3
    patience_counter = 0

    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch_x, _ in train_loader:
            batch_x = batch_x.to(device)
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_x)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * batch_x.size(0)
        
        train_loss /= len(train_loader.dataset)
        
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_x, _ in val_loader:
                batch_x = batch_x.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_x)
                val_loss += loss.item() * batch_x.size(0)
        val_loss /= len(val_loader.dataset)
        
        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f} - Val Loss: {val_loss:.6f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = model.state_dict()
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print("Early stopping triggered.")
                break

    if best_weights:
        model.load_state_dict(best_weights)
    
    return model

def score(model: nn.Module, X: np.ndarray) -> np.ndarray:
    """
    Returns the per-sample reconstruction error (MSE).
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()
    model.to(device)
    
    X_tensor = torch.tensor(X, dtype=torch.float32)
    
    # Process in batches to avoid OOM
    batch_size = 1024
    loader = DataLoader(TensorDataset(X_tensor), batch_size=batch_size, shuffle=False)
    
    errors = []
    criterion = nn.MSELoss(reduction='none')
    
    with torch.no_grad():
        for (batch_x,) in loader:
            batch_x = batch_x.to(device)
            outputs = model(batch_x)
            # MSE per row
            loss = criterion(outputs, batch_x).mean(dim=1)
            errors.append(loss.cpu().numpy())
            
    return np.concatenate(errors)
