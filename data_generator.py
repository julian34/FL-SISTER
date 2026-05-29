"""
data_generator.py
Generates synthetic scam-detection data and splits it across 2 clients (non-IID).

Features
--------
  0  msg_length          - character length of the message (normalized later)
  1  num_links           - number of URLs / hyperlinks
  2  has_phone_num       - binary: contains a phone number
  3  money_mention       - binary: mentions money / prize / reward
  4  urgency_words       - count of urgency words ("act now", "expire", …)
  5  all_caps_ratio      - fraction of upper-case characters
  6  exclamation_count   - number of "!" characters
  7  suspicious_keywords - count of suspicious keyword hits
  8  sender_known        - binary: sender is in contact list
  9  reply_requested     - binary: message asks for a reply / click

Label: 0 = legitimate, 1 = scam

Non-IID split
-------------
  Client 1  →  SMS-like distribution  (short msgs, phone nums, few links)
  Client 2  →  Email-like distribution (long msgs, many links, no phone nums)
"""

import os
import numpy as np
import pandas as pd

FEATURES = [
    "msg_length",
    "num_links",
    "has_phone_num",
    "money_mention",
    "urgency_words",
    "all_caps_ratio",
    "exclamation_count",
    "suspicious_keywords",
    "sender_known",
    "reply_requested",
]


def _make_samples(n: int, is_scam: bool, rng: np.random.Generator) -> np.ndarray:
    """Return an (n, 10) array for either scam or legitimate messages.

    Distributions are intentionally overlapping so the task is non-trivial
    and convergence curves are visible during federated training.
    """
    if is_scam:
        X = np.column_stack([
            rng.normal(140, 55, n).clip(20, 400),      # msg_length
            rng.poisson(1.8, n).clip(0, 10),            # num_links
            rng.binomial(1, 0.60, n),                   # has_phone_num
            rng.binomial(1, 0.72, n),                   # money_mention
            rng.poisson(2.2, n).clip(0, 10),            # urgency_words
            rng.beta(3, 2, n),                          # all_caps_ratio  (high)
            rng.poisson(1.8, n).clip(0, 10),            # exclamation_count
            rng.poisson(2.8, n).clip(0, 15),            # suspicious_keywords
            rng.binomial(1, 0.25, n),                   # sender_known    (low)
            rng.binomial(1, 0.78, n),                   # reply_requested (high)
        ])
    else:
        X = np.column_stack([
            rng.normal(190, 70, n).clip(20, 500),       # msg_length
            rng.poisson(0.6, n).clip(0, 5),             # num_links
            rng.binomial(1, 0.38, n),                   # has_phone_num
            rng.binomial(1, 0.18, n),                   # money_mention
            rng.poisson(0.7, n).clip(0, 5),             # urgency_words
            rng.beta(2, 5, n),                          # all_caps_ratio  (low)
            rng.poisson(0.6, n).clip(0, 5),             # exclamation_count
            rng.poisson(0.8, n).clip(0, 5),             # suspicious_keywords
            rng.binomial(1, 0.70, n),                   # sender_known    (high)
            rng.binomial(1, 0.30, n),                   # reply_requested (low)
        ])
    # Add Gaussian noise to every feature to increase class overlap
    X += rng.normal(0, 0.25, X.shape)
    return X


def generate_dataset(
    n_samples: int = 1000,
    scam_ratio: float = 0.40,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    n_scam = int(n_samples * scam_ratio)
    n_legit = n_samples - n_scam

    X = np.vstack([
        _make_samples(n_scam, is_scam=True, rng=rng),
        _make_samples(n_legit, is_scam=False, rng=rng),
    ])
    y = np.hstack([np.ones(n_scam), np.zeros(n_legit)])

    # Flip ~8 % of labels to simulate annotation noise
    noise_mask = rng.random(n_samples) < 0.08
    y[noise_mask] = 1.0 - y[noise_mask]

    idx = rng.permutation(n_samples)
    return X[idx].astype(np.float32), y[idx].astype(np.float32)


def generate_and_save(
    samples_per_client: int = 600,
    n_test: int = 300,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Create non-IID datasets for 2 clients + a shared test set, save to data/.
    Returns (X1, y1, X2, y2, X_test, y_test).
    """
    os.makedirs("data", exist_ok=True)

    # --- Client 1: SMS-like (shorter, more phone nums, fewer links) ---
    X1, y1 = generate_dataset(n_samples=samples_per_client, scam_ratio=0.45, seed=11)
    X1[:, 0] *= 0.65   # shorter messages
    X1[:, 1] *= 0.50   # fewer links
    X1[:, 2] = np.clip(X1[:, 2] * 1.25, 0, 1)   # more phone numbers

    # --- Client 2: Email-like (longer, more links, fewer phone nums) ---
    X2, y2 = generate_dataset(n_samples=samples_per_client, scam_ratio=0.35, seed=22)
    X2[:, 0] *= 1.60   # longer messages
    X2[:, 1] *= 1.80   # more links
    X2[:, 2] *= 0.40   # fewer phone numbers

    # --- Shared test set (balanced / general) ---
    X_test, y_test = generate_dataset(n_samples=n_test, scam_ratio=0.40, seed=99)

    # Persist to CSV
    for name, X, y in [("client1", X1, y1), ("client2", X2, y2), ("test", X_test, y_test)]:
        df = pd.DataFrame(X, columns=FEATURES)
        df["label"] = y
        df.to_csv(f"data/{name}_data.csv", index=False)

    # Summary
    print("[DataGen] Synthetic scam-detection data created")
    print(f"  Client 1 : {int(y1.sum())} scam / {int((y1 == 0).sum())} legit  ({samples_per_client} total)")
    print(f"  Client 2 : {int(y2.sum())} scam / {int((y2 == 0).sum())} legit  ({samples_per_client} total)")
    print(f"  Test set : {int(y_test.sum())} scam / {int((y_test == 0).sum())} legit  ({n_test} total)")
    print(f"  Files saved → data/client1_data.csv, client2_data.csv, test_data.csv")

    return X1, y1, X2, y2, X_test, y_test


if __name__ == "__main__":
    generate_and_save()
