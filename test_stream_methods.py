import asyncio
import os
from dotenv import load_dotenv
from commands.agent import AuraGuardAgent

load_dotenv()

async def main():
    agent_wrapper = AuraGuardAgent()
    agent = agent_wrapper._build_agent()
    
    try:
        async with agent:
            async with agent.run_stream("List 2 tables.") as result:
                # Let's see what methods are available on result
                print(f"Result type: {type(result)}")
                print(f"Methods: {[m for m in dir(result) if not m.startswith('_')]}")
                
                # Try to iterate
                try:
                    async for item in result:
                        print(f"Item: {item}")
                except Exception as e:
                    print(f"Iteration failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
