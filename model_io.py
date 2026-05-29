# model_io.py
import torch


def state_dict_to_payload(state_dict: dict) -> dict:
    return {
        key: value.detach().cpu().tolist()
        for key, value in state_dict.items()
    }


def payload_to_state_dict(payload: dict) -> dict:
    return {
        key: torch.tensor(value, dtype=torch.float32)
        for key, value in payload.items()
    }