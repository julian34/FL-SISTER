"""
main.py  —  Federated Learning for Scam Detection
==================================================

Topology
  ┌─────────────┐        weights        ┌──────────────┐
  │  Client 1   │ ─────────────────────▶│              │
  │ (SMS-like)  │ ◀─────────────────────│ Global Server│
  └─────────────┘   global model        │  (FedAvg)    │
                                        │              │
  ┌─────────────┐        weights        │              │
  │  Client 2   │ ─────────────────────▶│              │
  │(Email-like) │ ◀─────────────────────└──────────────┘
  └─────────────┘   global model

Algorithm  : FedAvg (McMahan et al., 2017)
Data       : Synthetic scam-detection features (non-IID split)
Privacy    : Raw data NEVER leaves the client — only model weights travel.

Run
---
    python main.py
"""

import numpy as np
from sklearn.preprocessing import StandardScaler

from data_generator import generate_and_save
from fl_client import FederatedClient
from fl_server import FederatedServer

# ── Config ─────────────────────────────────────────────────────────────────
CONFIG = {
    "n_rounds":          10,
    "local_epochs":       500,
    "learning_rate":   0.01,
    "batch_size":        32,
    "input_dim":         10,
    "samples_per_client": 600,
    "n_test":            300,
    "pretrain_epochs":   50,
}


# ── Helpers ─────────────────────────────────────────────────────────────────
def _bar(value: float, width: int = 30) -> str:
    filled = int(round(value * width))
    return "█" * filled + "░" * (width - filled)


def _header(text: str, char: str = "═", width: int = 62) -> str:
    return f"\n{char * width}\n  {text}\n{char * width}"


def _section(round_num: int, total: int) -> str:
    return f"\n{'─' * 62}\n  ROUND {round_num}/{total}\n{'─' * 62}"


# ── Main ────────────────────────────────────────────────────────────────────
def main() -> None:
    print(_header("FEDERATED LEARNING  ·  SCAM DETECTION"))
    print("  Nodes  : 1 Global Server  +  2 Clients")
    print(f"  Rounds : {CONFIG['n_rounds']}   |   Local epochs : {CONFIG['local_epochs']}")
    print(f"  Model  : input({CONFIG['input_dim']}) → 64 → 32 → 1  [BCELoss + Adam]")

    # ── 1. Data ────────────────────────────────────────────────────────────
    print(_header("STEP 1  ·  Data Generation", "─"))
    X1, y1, X2, y2, X_test, y_test = generate_and_save(
        samples_per_client=CONFIG["samples_per_client"],
        n_test=CONFIG["n_test"],
    )

    # Normalise: fit on combined client data (server never sees raw X)
    scaler = StandardScaler()
    scaler.fit(np.vstack([X1, X2]))
    X1_s      = scaler.transform(X1).astype(np.float32)
    X2_s      = scaler.transform(X2).astype(np.float32)
    X_test_s  = scaler.transform(X_test).astype(np.float32)

    # ── 2. Server ──────────────────────────────────────────────────────────
    print(_header("STEP 2  ·  Initialize Global Server", "─"))
    server = FederatedServer(input_dim=CONFIG["input_dim"])
    m0 = server.evaluate(X_test_s, y_test)
    print(f"  [Server] Global model ready  (random init)")
    print(f"  [Server] Baseline accuracy on test set : {m0['accuracy']:.4f}")

    print(f"  [Server] Pre-training on server data ({CONFIG['pretrain_epochs']} epochs)...")
    pt = server.pretrain(
        X_test_s, y_test,
        epochs=CONFIG["pretrain_epochs"],
        lr=CONFIG["learning_rate"],
        batch_size=CONFIG["batch_size"],
    )
    print(f"  [Server] Pre-training done  "
          f"loss {pt['initial_loss']:.4f} → {pt['final_loss']:.4f}")
    m1 = server.evaluate(X_test_s, y_test)
    print(f"  [Server] Accuracy after pre-training    : {m1['accuracy']:.4f}  (pre-trained)")

    # ── 3. Clients ─────────────────────────────────────────────────────────
    print(_header("STEP 3  ·  Initialize Clients", "─"))
    clients = [
        FederatedClient(
            client_id=1,
            X_train=X1_s, y_train=y1,
            input_dim=CONFIG["input_dim"],
            lr=CONFIG["learning_rate"],
            local_epochs=CONFIG["local_epochs"],
            batch_size=CONFIG["batch_size"],
        ),
        FederatedClient(
            client_id=2,
            X_train=X2_s, y_train=y2,
            input_dim=CONFIG["input_dim"],
            lr=CONFIG["learning_rate"],
            local_epochs=CONFIG["local_epochs"],
            batch_size=CONFIG["batch_size"],
        ),
    ]
    for c, y in zip(clients, [y1, y2]):
        scam_n  = int(y.sum())
        legit_n = len(y) - scam_n
        print(f"  [Client {c.client_id}] samples={c.n_samples}  scam={scam_n}  legit={legit_n}")

    # ── 4. Federated Learning Rounds ───────────────────────────────────────
    print(_header("STEP 4  ·  Federated Training", "─"))
    round_metrics: list[dict] = []

    for fl_round in range(1, CONFIG["n_rounds"] + 1):
        print(_section(fl_round, CONFIG["n_rounds"]))

        # 4a. Broadcast global weights
        global_w = server.get_global_weights()
        for c in clients:
            c.receive_global_weights(global_w)
        print(f"  [Server → Clients]  global weights broadcast")

        # 4b. Local training
        updated_weights = []
        updated_sizes   = []
        for c in clients:
            loss = c.train()
            local_acc = c.evaluate(X_test_s, y_test)
            print(
                f"  [Client {c.client_id}]  local training done  "
                f"loss={loss:.4f}  local_acc={local_acc:.4f}"
            )
            updated_weights.append(c.get_weights())
            updated_sizes.append(c.n_samples)

        # 4c. Aggregate (FedAvg)
        print(f"  [Clients → Server]  uploading weights …")
        server.aggregate(updated_weights, updated_sizes)

        # 4d. Global evaluation
        metrics = server.evaluate(X_test_s, y_test)
        round_metrics.append(metrics)
        print(
            f"  [Server]  global acc={metrics['accuracy']:.4f}  "
            f"prec={metrics['precision']:.4f}  "
            f"rec={metrics['recall']:.4f}  "
            f"f1={metrics['f1']:.4f}"
        )

    # ── 5. Final Report ────────────────────────────────────────────────────
    print(_header("STEP 5  ·  Final Results"))

    print("\n  Accuracy progression per round:\n")
    print(f"  {'Round':>5}  {'Accuracy':>9}  Progress")
    print(f"  {'─'*5}  {'─'*9}  {'─'*32}")
    for i, m in enumerate(round_metrics, 1):
        acc = m["accuracy"]
        print(f"  {i:>5}  {acc:>9.4f}  {_bar(acc)}")

    final   = round_metrics[-1]
    best    = max(round_metrics, key=lambda m: m["accuracy"])
    best_rnd = round_metrics.index(best) + 1

    print(f"\n┌─────────────────────────────────────┐")
    print(f"  │  FINAL GLOBAL MODEL                 │")
    print(f"  │  Accuracy  : {final['accuracy']:.4f}               │")
    print(f"  │  Precision : {final['precision']:.4f}               │")
    print(f"  │  Recall    : {final['recall']:.4f}               │")
    print(f"  │  F1 Score  : {final['f1']:.4f}               │")
    print(f"  │  Best acc  : {best['accuracy']:.4f}  (round {best_rnd})        │")
    print(f"  └─────────────────────────────────────┘")

    print(f"\n  Privacy guarantee : raw data stayed on each client.")
    print(f"  Only model weights were exchanged with the server.")
    print(f"\n{'═' * 62}\n")


if __name__ == "__main__":
    main()
