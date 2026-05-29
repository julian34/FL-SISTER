"""
fl_client.py
Federated Learning Client — holds local data, trains locally, and
exposes only model weights to the server (never raw data).

In a real deployment each client would run on a separate machine and
communicate via gRPC / REST.  Here everything lives in-process to keep
the demo self-contained.
"""

import copy
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from model import ScamDetector


class FederatedClient:
    def __init__(
        self,
        client_id: int,
        X_train: np.ndarray,
        y_train: np.ndarray,
        input_dim: int = 10,
        lr: float = 0.01,
        local_epochs: int = 5,
        batch_size: int = 32,
    ):
        self.client_id = client_id
        self.n_samples = len(X_train)
        self.lr = lr
        self.local_epochs = local_epochs

        # Local model (copy of global; weights replaced each round)
        self.model = ScamDetector(input_dim=input_dim)

        # Dataset
        X_t = torch.tensor(X_train, dtype=torch.float32)
        y_t = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
        dataset = TensorDataset(X_t, y_t)
        self.loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.loss_fn = nn.BCELoss()
        self.loss_history: list[float] = []

    # ------------------------------------------------------------------
    # Called by server at the start of every round
    # ------------------------------------------------------------------
    def receive_global_weights(self, global_weights: dict) -> None:
        """Load the latest global model weights sent by the server."""
        self.model.load_state_dict(copy.deepcopy(global_weights))

    # ------------------------------------------------------------------
    # Local training
    # ------------------------------------------------------------------
    def train(self) -> float:
        """
        Train on local data for `local_epochs` epochs.
        Returns average training loss.
        """
        self.model.train()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        total_loss = 0.0
        total_batches = 0

        for _ in range(self.local_epochs):
            for X_batch, y_batch in self.loader:
                optimizer.zero_grad()
                preds = self.model(X_batch)
                loss = self.loss_fn(preds, y_batch)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                total_batches += 1

        avg_loss = total_loss / max(total_batches, 1)
        self.loss_history.append(avg_loss)
        return avg_loss

    # ------------------------------------------------------------------
    # Weight exchange with server
    # ------------------------------------------------------------------
    def get_weights(self) -> dict:
        """Return a deep copy of local model weights (sent to server)."""
        return copy.deepcopy(self.model.state_dict())

    # ------------------------------------------------------------------
    # Local evaluation (for logging only — never shared with server)
    # ------------------------------------------------------------------
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> float:
        self.model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X_test, dtype=torch.float32)
            y_t = torch.tensor(y_test, dtype=torch.float32)
            preds = (self.model(X_t).squeeze() >= 0.5).float()
            accuracy = (preds == y_t).float().mean().item()
        return accuracy
