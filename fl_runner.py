import numpy as np
from sklearn.preprocessing import StandardScaler

from data_generator import generate_and_save
from fl_client import FederatedClient
from fl_server import FederatedServer

DEFAULT_CONFIG = {
    "n_rounds": 10,
    "local_epochs": 5,
    "learning_rate": 0.01,
    "batch_size": 32,
    "input_dim": 10,
    "samples_per_client": 600,
    "n_test": 300,
}


def run_federated(config: dict | None = None, verbose: bool = False) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if config:
        cfg.update(config)

    def log(msg: str) -> None:
        if verbose:
            print(msg)

    log("[Runner] Generating synthetic data...")
    X1, y1, X2, y2, X_test, y_test = generate_and_save(
        samples_per_client=cfg["samples_per_client"],
        n_test=cfg["n_test"],
    )

    scaler = StandardScaler()
    scaler.fit(np.vstack([X1, X2]))
    X1_s = scaler.transform(X1).astype(np.float32)
    X2_s = scaler.transform(X2).astype(np.float32)
    X_test_s = scaler.transform(X_test).astype(np.float32)

    server = FederatedServer(input_dim=cfg["input_dim"])

    clients = [
        FederatedClient(
            client_id=1,
            X_train=X1_s,
            y_train=y1,
            input_dim=cfg["input_dim"],
            lr=cfg["learning_rate"],
            local_epochs=cfg["local_epochs"],
            batch_size=cfg["batch_size"],
        ),
        FederatedClient(
            client_id=2,
            X_train=X2_s,
            y_train=y2,
            input_dim=cfg["input_dim"],
            lr=cfg["learning_rate"],
            local_epochs=cfg["local_epochs"],
            batch_size=cfg["batch_size"],
        ),
    ]

    baseline = server.evaluate(X_test_s, y_test)
    round_metrics = []

    for fl_round in range(1, cfg["n_rounds"] + 1):
        log(f"[Runner] Round {fl_round}/{cfg['n_rounds']}")

        global_w = server.get_global_weights()
        for client in clients:
            client.receive_global_weights(global_w)

        updated_weights = []
        updated_sizes = []
        client_logs = []
        for client in clients:
            loss = client.train()
            local_acc = client.evaluate(X_test_s, y_test)
            client_logs.append(
                {
                    "client_id": client.client_id,
                    "loss": float(loss),
                    "local_accuracy": float(local_acc),
                }
            )
            updated_weights.append(client.get_weights())
            updated_sizes.append(client.n_samples)

        server.aggregate(updated_weights, updated_sizes)
        metrics = server.evaluate(X_test_s, y_test)
        metrics["round"] = fl_round
        metrics["clients"] = client_logs
        round_metrics.append(metrics)

    final = round_metrics[-1]
    best = max(round_metrics, key=lambda m: m["accuracy"])

    return {
        "config": cfg,
        "baseline": baseline,
        "round_metrics": round_metrics,
        "final": {
            "accuracy": final["accuracy"],
            "precision": final["precision"],
            "recall": final["recall"],
            "f1": final["f1"],
        },
        "best": {
            "round": best["round"],
            "accuracy": best["accuracy"],
            "precision": best["precision"],
            "recall": best["recall"],
            "f1": best["f1"],
        },
    }
