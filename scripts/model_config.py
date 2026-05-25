import os
import json

def get_model_name(model_key: str, default: str = None) -> str:
    """
    Find workshop.config.json by walking up from this helper's location,
    and return the model name associated with the model_key.
    """
    curr = os.path.abspath(__file__)
    for _ in range(5):
        curr = os.path.dirname(curr)
        cfg_path = os.path.join(curr, "workshop.config.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path) as f:
                    config = json.load(f)
                    return config.get("models", {}).get(model_key, default)
            except Exception:
                pass
    return default
