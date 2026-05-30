import asyncio
import os
from dotenv import load_dotenv
from commands.agent import AuraGuardAgent

load_dotenv()

async def main():
    print("🛡️ Aura Guard: Tool Discovery Test")
    print("-" * 50)
    
    agent_wrapper = AuraGuardAgent()
    agent = agent_wrapper._build_agent()
    
    print(f"Model: {agent.model}")
    print("Discovering tools...")
    
    # In Pydantic AI, tools are registered in the agent
    # We can inspect the toolsets
    for toolset in agent.toolsets:
        print(f"\nToolset: {toolset}")
        # Note: toolsets are async providers in pydantic-ai
        # We need to see what they provide
    
    # Let's try to run a query that specifically asks for a tool call
    # and see the raw parts if possible
    try:
        async with agent:
            result = await agent.run("Use a tool to list the first 5 tables in the catalog.")
            print("\nResult:")
            print(result.output)
            print("\nUsage:")
            print(result.usage())
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
