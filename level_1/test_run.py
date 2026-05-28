import asyncio
import os
import sys
import logging

# Enable full info logging to see tool executions
logging.basicConfig(
    format="[%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai.types import Content, Part
from agent.agent import root_agent

async def main():
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()
    
    async with Runner(
        agent=root_agent,
        session_service=session_service,
        memory_service=memory_service,
        app_name="mission-analysis-ai",
        auto_create_session=True
    ) as runner:
        print("Starting Diagnostic Run...")
        async for event in runner.run_async(
            user_id="user",
            session_id="session",
            new_message=Content(role="user", parts=[Part(text="Analyze the evidence, coordinate with your specialists to determine the biome, and call the confirm_location tool to activate my rescue beacon.")])
        ):
            print(f"\n--- EVENT: {type(event).__name__} ---")
            if hasattr(event, "text") and event.text:
                print(f"Text: {event.text}")
            if hasattr(event, "content") and event.content:
                print(f"Content: {event.content}")
            if hasattr(event, "parts") and event.parts:
                print(f"Parts: {event.parts}")

if __name__ == "__main__":
    asyncio.run(main())
