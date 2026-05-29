"""
ScamDetector - Simple feedforward neural network for binary scam classification.

Input features (10):
  msg_length, num_links, has_phone_num, money_mention, urgency_words,
  all_caps_ratio, exclamation_count, suspicious_keywords, sender_known,
  reply_requested

Output: probability [0, 1]  →  0 = legitimate, 1 = scam
"""

import torch
import torch.nn as nn


class ScamDetector(nn.Module):
    def __init__(self, input_dim: int = 10):
        super(ScamDetector, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)
