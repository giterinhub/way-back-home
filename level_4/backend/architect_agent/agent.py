from google.adk.agents.llm_agent import Agent
import os
import redis

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


REDIS_IP = os.environ.get('REDIS_HOST', 'localhost')
r = redis.Redis(host=REDIS_IP, port=6379, decode_responses=True)

def lookup_schematic_tool(drive_name: str) -> list[str]:
    """Returns the ordered list of parts for a drive from local Redis."""
    
    # Logic to clean input like "TARGET: X" -> "X"
    clean_name = drive_name.replace("TARGET:", "").replace("TARGET", "").strip()
    clean_name = clean_name.replace(":", "").strip()
    
    # LRANGE gets all items in the list (index 0 to -1)
    result = r.lrange(clean_name, 0, -1)
    
    if not result:
        print(f"[ARCHITECT] Error: Drive ID '{clean_name}' not found in Redis.")
        return ["ERROR: Drive ID not found."]
    
    print(f"[ARCHITECT] Returning schematic for {clean_name}: {result}")
    return result


root_agent = Agent(
    model=get_model_name("flash", "gemini-3.5-flash-preview"),
    name='root_agent',
    description='A helpful assistant for user questions.',
    instruction='''SYSTEM ROLE: Database API.
    INPUT: Text string (Drive Name).
    TASK: Run `lookup_schematic_tool`.
    OUTPUT: Return ONLY the raw list from the tool.
    CONSTRAINT: Do NOT add conversational text.
    ''',
    tools=[lookup_schematic_tool],
)