from threading import Lock

from fastapi import FastAPI
from pydantic import BaseModel

from fl_runner import DEFAULT_CONFIG, run_federated

app = FastAPI(title="FL Scam Detection API", version="1.0.0")

_last_result = None
_run_lock = Lock()


class TrainRequest(BaseModel):
    n_rounds: int | None = None
    local_epochs: int | None = None
    learning_rate: float | None = None
    batch_size: int | None = None
    samples_per_client: int | None = None
    n_test: int | None = None


@app.get("/")
def root() -> dict:
    return {
        "message": "Federated Learning Scam Detection API",
        "endpoints": ["/health", "/train", "/last-result"],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/train")
def train(req: TrainRequest) -> dict:
    global _last_result

    overrides = {
        key: value
        for key, value in req.model_dump().items()
        if value is not None
    }

    cfg = dict(DEFAULT_CONFIG)
    cfg.update(overrides)

    with _run_lock:
        _last_result = run_federated(config=cfg, verbose=False)

    return {
        "message": "training completed",
        "config": _last_result["config"],
        "final": _last_result["final"],
        "best": _last_result["best"],
        "rounds": len(_last_result["round_metrics"]),
    }


@app.get("/last-result")
def last_result() -> dict:
    if _last_result is None:
        return {
            "message": "no training has been run yet",
            "hint": "POST /train to start federated learning",
        }
    return _last_result
