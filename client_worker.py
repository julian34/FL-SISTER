# client_worker.py
import os
import time

import numpy as np
import pandas as pd
import requests
from sklearn.preprocessing import StandardScaler

from fl_client import FederatedClient
from model_io import state_dict_to_payload, payload_to_state_dict


CLIENT_ID = os.getenv("CLIENT_ID", "1")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
DATA_PATH = os.getenv("DATA_PATH", "data/client1_data.csv")

LOCAL_EPOCHS = int(os.getenv("LOCAL_EPOCHS", "5"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))
LEARNING_RATE = float(os.getenv("LEARNING_RATE", "0.01"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))


def load_local_dataset(path: str):
    df = pd.read_csv(path)

    if "label" not in df.columns:
        raise ValueError("Dataset harus memiliki kolom 'label'.")

    X = df.drop(columns=["label"]).values.astype(np.float32)
    y = df["label"].values.astype(np.float32)

    # Normalisasi dilakukan lokal di client.
    # Ini lebih sesuai untuk FL dibanding fit scaler dari gabungan data semua client.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X).astype(np.float32)

    return X_scaled, y


def main():
    print(f"[Client {CLIENT_ID}] Loading local data: {DATA_PATH}")
    X_train, y_train = load_local_dataset(DATA_PATH)

    client = FederatedClient(
        client_id=int(CLIENT_ID),
        X_train=X_train,
        y_train=y_train,
        input_dim=X_train.shape[1],
        lr=LEARNING_RATE,
        local_epochs=LOCAL_EPOCHS,
        batch_size=BATCH_SIZE,
    )

    last_submitted_round = 0

    print(f"[Client {CLIENT_ID}] Connected to server: {SERVER_URL}")
    print(f"[Client {CLIENT_ID}] Local samples: {client.n_samples}")

    while True:
        try:
            response = requests.get(f"{SERVER_URL}/global-model", timeout=20)
            response.raise_for_status()
            global_payload = response.json()

            if global_payload.get("completed"):
                print(f"[Client {CLIENT_ID}] Training completed by server.")
                break

            round_number = int(global_payload["round"])

            if round_number <= last_submitted_round:
                time.sleep(POLL_SECONDS)
                continue

            print(f"[Client {CLIENT_ID}] Starting local training for round {round_number}")

            global_weights = payload_to_state_dict(global_payload["weights"])
            client.receive_global_weights(global_weights)

            loss = client.train()
            local_weights = client.get_weights()

            update_payload = {
                "client_id": CLIENT_ID,
                "round": round_number,
                "n_samples": client.n_samples,
                "weights": state_dict_to_payload(local_weights),
                "loss": float(loss),
            }

            submit_response = requests.post(
                f"{SERVER_URL}/submit-update",
                json=update_payload,
                timeout=60,
            )
            submit_response.raise_for_status()

            result = submit_response.json()
            last_submitted_round = round_number

            print(
                f"[Client {CLIENT_ID}] Round {round_number} submitted | "
                f"loss={loss:.4f} | server={result}"
            )

            time.sleep(POLL_SECONDS)

        except requests.RequestException as error:
            print(f"[Client {CLIENT_ID}] Server belum siap / koneksi gagal: {error}")
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()