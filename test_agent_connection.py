import asyncio
import os
from dotenv import load_dotenv
from commands.agent import AuraGuardAgent

load_dotenv(override=True)

async def main():
    print("🛡️ Aura Guard: Native MCP Connection Test (Doctor Mode)")
    print("-" * 50)
    
    agent = AuraGuardAgent()
    
    # We want to see if the agent can successfully list tables via Coral MCP
    test_query = "What SRE data sources can you see through Coral? List the schemas and a few tables."
    
    print(f"Agent Model: {agent.model}")
    print(f"Coral Bin: {agent.coral_bin}")
    print(f"Running Test Query: '{test_query}'...")
    print("-" * 50)
    
    # Mock event handler to show live tool calls in the terminal
    async def mock_on_event(event_type, data):
        if event_type == "query_start":
            print(f"\n[INTERNAL AGENT SQL]:\n{data.get('sql')}\n")
        elif event_type == "query_success":
            print("[SQL SUCCESS]")

    try:
        report = await agent.investigate(test_query, on_event=mock_on_event)
        print("-" * 50)
        print("Final Agent Report:")
        print(report)
        print("-" * 50)
        print("✅ Connection Test Passed!")
    except Exception as e:
        print("-" * 50)
        print(f"❌ Connection Test Failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
