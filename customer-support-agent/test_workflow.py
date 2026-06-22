import asyncio
from app.agent import app
from google.adk.agents import Context
from google.adk.sessions import Session
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event_actions import EventActions

async def main():
    session = Session(id="test_session", app_name="test", user_id="test")
    invocation_context = InvocationContext(session=session)
    ctx = Context(invocation_context=invocation_context)
    
    # Test shipping query
    print("Testing shipping query...")
    events = app.root_agent.run(ctx=ctx, node_input="What are your shipping rates?")
    async for event in events:
        if hasattr(event, "output") and event.output:
            print("Shipping agent response:", event.output)

    # Test unrelated query
    print("\nTesting unrelated query...")
    events2 = app.root_agent.run(ctx=ctx, node_input="What is the capital of France?")
    async for event in events2:
        if hasattr(event, "output") and event.output:
            print("Decline node response:", event.output)

if __name__ == "__main__":
    asyncio.run(main())
