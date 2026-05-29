# server_api.py
import os
import threading
from typing import Any

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from fl_server import FederatedServer
from model_io import state_dict_to_payload, payload_to_state_dict


NUM_CLIENTS = int(os.getenv("NUM_CLIENTS", "2"))
N_ROUNDS = int(os.getenv("N_ROUNDS", "10"))
INPUT_DIM = int(os.getenv("INPUT_DIM", "10"))

app = FastAPI(title="Federated Learning Scam Detection Server")

server = FederatedServer(input_dim=INPUT_DIM)
lock = threading.Lock()
submissions: dict[int, dict[str, dict]] = {}

os.makedirs("checkpoints", exist_ok=True)


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

        aggregated = False

        if len(round_bucket) >= NUM_CLIENTS:
            client_items = list(round_bucket.values())

            client_weights = [item["weights"] for item in client_items]
            client_sizes = [item["n_samples"] for item in client_items]

            server.aggregate(client_weights, client_sizes)
            aggregated = True

            checkpoint_path = f"checkpoints/global_round_{server.round}.pt"
            torch.save(server.global_model.state_dict(), checkpoint_path)

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