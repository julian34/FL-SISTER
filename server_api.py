# server_api.py
import os
import threading
from typing import Any

import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sklearn.preprocessing import StandardScaler
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Gauge

from fl_server import FederatedServer
from model_io import state_dict_to_payload, payload_to_state_dict


NUM_CLIENTS = int(os.getenv("NUM_CLIENTS", "2"))
N_ROUNDS = int(os.getenv("N_ROUNDS", "10"))
INPUT_DIM = int(os.getenv("INPUT_DIM", "10"))
PRETRAIN_EPOCHS = int(os.getenv("PRETRAIN_EPOCHS", "50"))
PRETRAIN_DATA_PATH = os.getenv("PRETRAIN_DATA_PATH", "data/test_data.csv")

app = FastAPI(title="Federated Learning Scam Detection Server")

Instrumentator().instrument(app).expose(app)

CLIENT_UPDATE_TOTAL = Counter(
    "fl_client_update_total",
    "Total update yang dikirim client ke FL server",
    ["client_id", "round"]
)

CLIENT_LOSS = Gauge(
    "fl_client_loss",
    "Loss terakhir dari setiap client",
    ["client_id"]
)

FL_COLLECTED_UPDATES = Gauge(
    "fl_collected_updates",
    "Jumlah update client yang sudah terkumpul pada round aktif"
)

FL_COMPLETED_ROUND = Gauge(
    "fl_completed_round",
    "Round federated learning yang sudah selesai"
)

server = FederatedServer(input_dim=INPUT_DIM)
lock = threading.Lock()
submissions: dict[int, dict[str, dict]] = {}

os.makedirs("checkpoints", exist_ok=True)

# ── Server pre-training on startup ─────────────────────────────────────────
if PRETRAIN_EPOCHS > 0 and os.path.exists(PRETRAIN_DATA_PATH):
    print(f"[Server] Loading pre-training data from: {PRETRAIN_DATA_PATH}")
    _df = pd.read_csv(PRETRAIN_DATA_PATH)
    _X = _df.drop(columns=["label"]).values.astype(np.float32)
    _y = _df["label"].values.astype(np.float32)
    _scaler = StandardScaler()
    _X_scaled = _scaler.fit_transform(_X).astype(np.float32)
    print(f"[Server] Pre-training global model ({PRETRAIN_EPOCHS} epochs, {len(_X)} samples)...")
    _pt = server.pretrain(_X_scaled, _y, epochs=PRETRAIN_EPOCHS, lr=0.01, batch_size=32)
    print(f"[Server] Pre-training done  loss {_pt['initial_loss']:.4f} → {_pt['final_loss']:.4f}")
    torch.save(server.global_model.state_dict(), "checkpoints/global_init.pt")
    print("[Server] Initial checkpoint saved: checkpoints/global_init.pt")
else:
    print(f"[Server] Pre-training skipped (PRETRAIN_EPOCHS={PRETRAIN_EPOCHS}, "
          f"data exists={os.path.exists(PRETRAIN_DATA_PATH)})")



class ClientUpdate(BaseModel):
    client_id: str
    round: int
    n_samples: int
    weights: dict[str, Any]
    loss: float | None = None


@app.get("/")
def root():
    return {
        "message": "FL Server is running",
        "num_clients": NUM_CLIENTS,
        "n_rounds": N_ROUNDS,
        "current_completed_round": server.round,
    }


@app.get("/status")
def status():
    with lock:
        next_round = server.round + 1

        if server.round >= N_ROUNDS:
            return {
                "completed": True,
                "completed_round": server.round,
                "message": "Federated training completed",
            }

        collected = len(submissions.get(next_round, {}))

        return {
            "completed": False,
            "completed_round": server.round,
            "next_round": next_round,
            "expected_clients": NUM_CLIENTS,
            "collected_updates": collected,
        }


@app.get("/global-model")
def get_global_model():
    with lock:
        if server.round >= N_ROUNDS:
            return {
                "completed": True,
                "completed_round": server.round,
            }

        return {
            "completed": False,
            "round": server.round + 1,
            "weights": state_dict_to_payload(server.get_global_weights()),
        }


@app.post("/submit-update")
def submit_update(update: ClientUpdate):
    with lock:
        if server.round >= N_ROUNDS:
            return {
                "accepted": False,
                "completed": True,
                "message": "Training already completed",
            }

        expected_round = server.round + 1

        if update.round < expected_round:
            return {
                "accepted": False,
                "reason": "stale_round",
                "server_expected_round": expected_round,
            }

        if update.round > expected_round:
            return {
                "accepted": False,
                "reason": "server_not_ready",
                "server_expected_round": expected_round,
            }

        round_bucket = submissions.setdefault(update.round, {})
        round_bucket[update.client_id] = {
            "weights": payload_to_state_dict(update.weights),
            "n_samples": update.n_samples,
            "loss": update.loss,
        }

        CLIENT_UPDATE_TOTAL.labels(
            client_id=update.client_id,
            round=str(update.round)
        ).inc()

        if update.loss is not None:
            CLIENT_LOSS.labels(client_id=update.client_id).set(update.loss)

        FL_COLLECTED_UPDATES.set(len(round_bucket))

        aggregated = False

        if len(round_bucket) >= NUM_CLIENTS:
            client_items = list(round_bucket.values())

            client_weights = [item["weights"] for item in client_items]
            client_sizes = [item["n_samples"] for item in client_items]

            server.aggregate(client_weights, client_sizes)
            aggregated = True

            checkpoint_path = f"checkpoints/global_round_{server.round}.pt"
            torch.save(server.global_model.state_dict(), checkpoint_path)

            FL_COMPLETED_ROUND.set(server.round)

            del submissions[update.round]

        return {
            "accepted": True,
            "aggregated": aggregated,
            "completed_round": server.round,
            "message": (
                "Round aggregated"
                if aggregated
                else "Update received, waiting for other clients"
            ),
        }


@app.post("/reset")
def reset_training():
    """Reset server state so a new training session can begin from scratch."""
    global submissions

    with lock:
        server.round = 0
        server.accuracy_history.clear()
        submissions = {}

        checkpoint_path = "checkpoints/global_init.pt"
        if os.path.exists(checkpoint_path):
            state = torch.load(checkpoint_path, map_location="cpu")
            server.global_model.load_state_dict(state)
            loaded_checkpoint = True
        else:
            # Re-initialise with fresh random weights
            server.global_model = server.global_model.__class__(input_dim=INPUT_DIM)
            loaded_checkpoint = False

        server.global_model.eval()
        FL_COMPLETED_ROUND.set(0)
        FL_COLLECTED_UPDATES.set(0)

    return {
        "reset": True,
        "loaded_checkpoint": loaded_checkpoint,
        "message": "Server reset. Training can now be started again from round 1.",
    }