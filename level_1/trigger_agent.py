import asyncio
import os
import sys

# Force Vertex AI to use global location for model availability
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai.types import Content, Part

# Ensure Level 1 directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
            user_id = "user"
            session_id = "session"
            
            print("🤖 AGENT ANALYSIS RUNNING:")
            print("============================================================\n")
            
            # Run agent query through the runner async generator and stream results
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
                    
            print("\n============================================================\n")
            print("✅ Analysis complete! Check the map at https://erinl.space to see your beacon!")
        
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")
        print("   Make sure your environment variables are loaded: source ../set_env.sh")

if __name__ == "__main__":
    asyncio.run(main())
