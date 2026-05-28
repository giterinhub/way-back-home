import asyncio
import os
import sys
import logging
from unittest.mock import MagicMock, AsyncMock

# Enable info logging
logging.basicConfig(
    format="[%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)

# Mock environment variables
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["MCP_SERVER_URL"] = "http://localhost:8080"
os.environ["PARTICIPANT_ID"] = "f0ea691f"
os.environ["BACKEND_URL"] = "https://api.erinl.space"
os.environ["GOOGLE_CLOUD_PROJECT"] = "waybackhome-497709"
os.environ["GEMINI_API_KEY"] = "mock-key"
os.environ["GOOGLE_API_KEY"] = "mock-key"

# Ensure level_1 is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock google.auth
import google.auth
mock_cred = MagicMock()
mock_cred.token = "mock-token"
mock_cred.refresh = MagicMock()
google.auth.default = MagicMock(return_value=(mock_cred, "waybackhome-497709"))

# Mock responses
from google.genai.types import GenerateContentResponse, Candidate, Content, Part
part = Part(text='{"primary_star": "green_pulsar", "nebula_type": "purple_magenta", "stellar_color": "green_purple", "description": "pulsar"}')
content = Content(role="model", parts=[part])
candidate = Candidate(content=content)
mock_response = GenerateContentResponse(candidates=[candidate], model_version="gemini-3.5-flash")

# Mock Client's internal generation
from google.genai.client import Client

# Create mock objects
mock_models = MagicMock()
mock_models.generate_content = MagicMock(return_value=mock_response)
mock_models.generate_content_async = AsyncMock(return_value=mock_response)

mock_aio = MagicMock()
mock_aio.models = MagicMock()
mock_aio.models.generate_content = AsyncMock(return_value=mock_response)

# Override read-only properties
Client.models = property(lambda self: mock_models)
Client.aio = property(lambda self: mock_aio)

# Correctly mock __init__ to set _api_client
def mock_client_init(self, *args, **kwargs):
    self._api_client = MagicMock()
    self._api_client.vertexai = False
    self._api_client.location = "global"
    self._api_client.project = "waybackhome-497709"
    self._api_client.http_options = MagicMock()

Client.__init__ = mock_client_init

# Import ADK tools
from google.adk.tools import FunctionTool
import agent.tools.mcp_tools as mcp_tools
import agent.tools.star_tools as star_tools

# Define mock tools
def analyze_geological(image_url: str) -> dict:
    print(f"\n[Mock Tool] analyze_geological called for: {image_url}")
    return {
        "biome": "BIOLUMINESCENT",
        "description": "soil base featuring glowing mycelial network.",
        "minerals": ["Phosphorescent silicates"]
    }

def analyze_botanical(flora_url: str) -> dict:
    print(f"\n[Mock Tool] analyze_botanical called for: {flora_url}")
    return {
        "biome": "BIOLUMINESCENT",
        "description": "glowing purple fungi.",
        "confidence": "70%"
    }

def extract_star_features(image_url: str) -> dict:
    print(f"\n[Mock Tool] extract_star_features called for: {image_url}")
    return {
        "primary_star": "green_pulsar",
        "nebula_type": "purple_magenta",
        "stellar_color": "green_purple",
        "description": "green pulsar."
    }

def execute_query(query: str) -> list:
    print(f"\n[Mock Tool] execute_query called with SQL: {query}")
    return [{"quadrant": "SW", "biome": "BIOLUMINESCENT"}]

mock_geological_tool = FunctionTool(analyze_geological)
mock_botanical_tool = FunctionTool(analyze_botanical)
mock_extract_stars_tool = FunctionTool(extract_star_features)
mock_execute_query_tool = FunctionTool(execute_query)

mcp_tools.get_mcp_toolset = lambda: mock_geological_tool
mcp_tools.get_geological_tool = lambda: mock_geological_tool
mcp_tools.get_botanical_tool = lambda: mock_botanical_tool

star_tools.get_bigquery_mcp_toolset = lambda: mock_execute_query_tool
star_tools.extract_star_features_tool = mock_extract_stars_tool
star_tools.extract_star_features = extract_star_features

# Import root agent and runner
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from agent.agent import root_agent

import requests
def mock_patch(url, *args, **kwargs):
    print(f"\n🚀 [requests.patch] INTERCEPTED: {url} with args={args}, kwargs={kwargs}")
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"status": "success"}
    return resp
requests.patch = mock_patch

async def main():
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    
    from google.adk.apps.app import ResumabilityConfig
    async with Runner(
        agent=root_agent,
        session_service=session_service,
        memory_service=memory_service,
        app_name="mission-analysis-ai",
        auto_create_session=True
    ) as runner:
        runner.resumability_config = ResumabilityConfig(is_resumable=True)
        print("\n=== STARTING MOCK RUN ===")
        user_id = "user"
        session_id = "session"
        
        # We run the async flow with the elegant multi-turn resumption loop
        from google.genai import types
        
        last_invocation_id = None
        root_agent_finished = False
        
        print("\n--- Initial Turn ---")
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text="Analyze the evidence, coordinate with your specialists to determine the biome, and call the confirm_location tool to activate my rescue beacon.")])
        ):
            print(f"Event: {type(event).__name__}")
            if hasattr(event, "text") and event.text:
                print(f"  Text: {event.text}")
            if event.invocation_id:
                last_invocation_id = event.invocation_id
            if event.author == root_agent.name and event.actions and event.actions.end_of_agent:
                root_agent_finished = True
                
        # If the orchestrator agent didn't complete (e.g., paused after sub-agent finished), resume it
        turn_count = 1
        while not root_agent_finished and last_invocation_id:
            turn_count += 1
            print(f"\n--- Resuming Turn {turn_count} ---")
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                invocation_id=last_invocation_id
            ):
                print(f"Event: {type(event).__name__}")
                if hasattr(event, "text") and event.text:
                    print(f"  Text: {event.text}")
                if event.invocation_id:
                    last_invocation_id = event.invocation_id
                if event.author == root_agent.name and event.actions and event.actions.end_of_agent:
                    root_agent_finished = True
                
        print("\n=== MOCK RUN COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(main())
