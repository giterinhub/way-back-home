import asyncio
import os
import sys

# Ensure Level 1 directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.agent import root_agent

async def main():
    print("🚀 Triggering the Mission Analysis AI consensus crew...")
    print("   Please make sure your FastMCP server is running on port 8080!\n")
    
    try:
        # Run the agent with the location triangulation prompt
        response = await root_agent.run("Analyze the evidence and confirm my location.")
        
        print("\n============================================================")
        print("🤖 AGENT RESPONSE:")
        print("============================================================")
        print(response.text)
        print("============================================================\n")
        
        print("✅ Analysis complete! Check the map at https://erinl.space to see your beacon!")
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")
        print("   Make sure your environment variables are loaded: source ../set_env.sh")

if __name__ == "__main__":
    asyncio.run(main())
