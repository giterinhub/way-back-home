import asyncio
import os
import sys

# Force Vertex AI to use global location for model availability
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

# Force ADK to use Vertex AI instead of AI Studio (Gemini Developer API)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

# Ensure Level 1 directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load GCP Project and Participant details dynamically from config.json to eliminate sourcing set_env.sh requirement
try:
    from config_utils import get_project_id, get_participant_id, get_backend_url
    if not os.environ.get("GOOGLE_CLOUD_PROJECT") and not os.environ.get("PROJECT_ID"):
        proj_id = get_project_id()
        if proj_id:
            os.environ["GOOGLE_CLOUD_PROJECT"] = proj_id
            os.environ["PROJECT_ID"] = proj_id
    if not os.environ.get("PARTICIPANT_ID"):
        part_id = get_participant_id()
        if part_id:
            os.environ["PARTICIPANT_ID"] = part_id
    if not os.environ.get("BACKEND_URL"):
        back_url = get_backend_url()
        if back_url:
            os.environ["BACKEND_URL"] = back_url
except Exception:
    pass

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai.types import Content, Part

from agent.agent import root_agent

async def main():
    print("🚀 Triggering the Mission Analysis AI consensus crew...")
    print("   Please make sure your FastMCP server is running on port 8080!\n")
    
    try:
        # Initialize standard ADK services
        session_service = InMemorySessionService()
        memory_service = InMemoryMemoryService()
        
        # Initialize standard ADK Runner lifecycle using context manager for graceful cleanup
        async with Runner(
            agent=root_agent,
            session_service=session_service,
            memory_service=memory_service,
            app_name="mission-analysis-ai",
            auto_create_session=True
        ) as runner:
            from google.adk.apps.app import ResumabilityConfig
            runner.resumability_config = ResumabilityConfig(is_resumable=True)
            
            user_id = "user"
            session_id = "session"
            
            print("🤖 AGENT ANALYSIS RUNNING:")
            print("============================================================\n")
            
            last_invocation_id = None
            root_agent_finished = False
            
            # Run initial agent query through the runner async generator and stream results
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=Content(role="user", parts=[Part(text="Analyze the evidence, coordinate with your specialists to determine the biome, and call the confirm_location tool to activate my rescue beacon.")])
            ):
                try:
                    if hasattr(event, "text") and event.text:
                        print(event.text, end="", flush=True)
                    elif hasattr(event, "content") and event.content:
                        for part in event.content.parts:
                            if hasattr(part, "text") and part.text:
                                print(part.text, end="", flush=True)
                    elif hasattr(event, "parts"):
                        for part in event.parts:
                            if hasattr(part, "text") and part.text:
                                print(part.text, end="", flush=True)
                except Exception as e:
                    print(f"\n[Error processing event: {e}]", flush=True)
                
                if event.invocation_id:
                    last_invocation_id = event.invocation_id
                if event.author == root_agent.name and event.actions and event.actions.end_of_agent:
                    root_agent_finished = True

            # If the orchestrator agent paused or was suspended (e.g. waiting for parallel specialists to finish), resume it
            while not root_agent_finished and last_invocation_id:
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    invocation_id=last_invocation_id
                ):
                    try:
                        if hasattr(event, "text") and event.text:
                            print(event.text, end="", flush=True)
                        elif hasattr(event, "content") and event.content:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    print(part.text, end="", flush=True)
                        elif hasattr(event, "parts"):
                            for part in event.parts:
                                if hasattr(part, "text") and part.text:
                                    print(part.text, end="", flush=True)
                    except Exception as e:
                        print(f"\n[Error processing event: {e}]", flush=True)
                    
                    if event.invocation_id:
                        last_invocation_id = event.invocation_id
                    if event.author == root_agent.name and event.actions and event.actions.end_of_agent:
                        root_agent_finished = True
                    
            print("\n============================================================\n")
            print("✅ Analysis complete! Check the map at https://erinl.space to see your beacon!")
        
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")
        print("   Make sure your environment variables are loaded: source ../set_env.sh")

if __name__ == "__main__":
    asyncio.run(main())
