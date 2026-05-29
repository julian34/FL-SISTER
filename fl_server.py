"""
fl_server.py
Federated Learning Global Server — aggregates client weights using FedAvg
and maintains the global model.

FedAvg (McMahan et al., 2017)
  w_global = Σ (n_k / N) * w_k
  where n_k = samples on client k, N = total samples across all clients.
"""

import copy
import torch
import numpy as np

from model import ScamDetector


class FederatedServer:
    def __init__(self, input_dim: int = 10):
        self.global_model = ScamDetector(input_dim=input_dim)
        self.round = 0
        self.accuracy_history: list[float] = []

    # ------------------------------------------------------------------
    # Distribute
    # ------------------------------------------------------------------
    def get_global_weights(self) -> dict:
        """Return a copy of the current global weights for clients."""
        return copy.deepcopy(self.global_model.state_dict())

    # ------------------------------------------------------------------
    # Aggregate  (FedAvg)
    # ------------------------------------------------------------------
    def aggregate(
        self,
        client_weights: list[dict],
        client_sizes: list[int],
    ) -> None:
        """
        Weighted average of client weights proportional to dataset size.

        Parameters
        ----------
        client_weights : list of state_dicts from each client
        client_sizes   : number of training samples on each client
        """
        assert len(client_weights) == len(client_sizes), \
            "Mismatch between weights and sizes lists."

        total = sum(client_sizes)
        avg_state = {}

        for key in client_weights[0].keys():
            # Stack and compute weighted sum
            weighted = torch.stack([
                w[key].float() * (n / total)
                for w, n in zip(client_weights, client_sizes)
            ])
            avg_state[key] = weighted.sum(dim=0)

        self.global_model.load_state_dict(avg_state)
        self.round += 1

    # ------------------------------------------------------------------
    # Evaluate global model
    # ------------------------------------------------------------------
    def evaluate(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray,
    ) -> dict:
        """
        Evaluate the global model and return a metrics dict:
        accuracy, precision, recall, f1.
        """
        self.global_model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X_test, dtype=torch.float32)
            y_t = torch.tensor(y_test, dtype=torch.float32)
            probs = self.global_model(X_t).squeeze()
            preds = (probs >= 0.5).float()

        tp = float(((preds == 1) & (y_t == 1)).sum())
        fp = float(((preds == 1) & (y_t == 0)).sum())
        fn = float(((preds == 0) & (y_t == 1)).sum())
        tn = float(((preds == 0) & (y_t == 0)).sum())

        accuracy  = (tp + tn) / (tp + tn + fp + fn + 1e-9)
        precision = tp / (tp + fp + 1e-9)
        recall    = tp / (tp + fn + 1e-9)
        f1        = 2 * precision * recall / (precision + recall + 1e-9)

        self.accuracy_history.append(accuracy)
        return {
            "accuracy":  accuracy,
            "precision": precision,
            "recall":    recall,
            "f1":        f1,
        }
