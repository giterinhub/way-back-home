
def get_model_name(model_key: str, default: str) -> str:
    import os, json
    curr = os.path.abspath(__file__)
    for _ in range(5):
        curr = os.path.dirname(curr)
        cfg_path = os.path.join(curr, "workshop.config.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path) as f:
                    return json.load(f).get("models", {}).get(model_key, default)
            except Exception:
                pass
    return default

import os
from google.adk.agents import Agent
from typing import List, Optional, Callable, Dict, Any
from dotenv import load_dotenv

load_dotenv()


#REPLACE TOOLS

#REPLACE_MODEL

root_agent = Agent(
    name="biometric_agent",
    model=MODEL_ID,
    #TOOL CONFIG,
    instruction="""
    #REPLACE INSTRUCTIONS
    """
)