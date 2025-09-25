# /agents/MOCKS.py

from .contracts import AgentOutput
import asyncio

async def mock_search_agent(prompt: str) -> AgentOutput:
    """Mock for finding information online."""
    print(f" MOCK SEARCH AGENT: Received prompt -> '{prompt}'")
    await asyncio.sleep(1) # Simulate network latency
    if "fail" in prompt.lower():
        return AgentOutput(status="failed", error="Could not find information online.")
    return AgentOutput(
        status="completed",
        result="Found 'Ristorante Bellissimo'. Website: bellissimo.de, Phone: +49 89 1234567"
    )

async def mock_browser_agent(prompt: str) -> AgentOutput:
    """Mock for web scraping and form filling."""
    print(f" MOCK BROWSER AGENT: Received prompt -> '{prompt}'")
    await asyncio.sleep(2) # Simulate browser actions
    prompt+="fail"
    if "fail" in prompt.lower():
        return AgentOutput(status="failed", error="The online reservation form is broken.")
    return AgentOutput(status="completed", result="Successfully submitted the reservation for 2 people.")

async def mock_calendar_agent(prompt: str) -> AgentOutput:
    """Mock for creating calendar events."""
    print(f" MOCK CALENDAR AGENT: Received prompt -> '{prompt}'")
    await asyncio.sleep(1)
    return AgentOutput(status="completed", result="Calendar event has been created.")

async def mock_calling_agent(prompt: str) -> AgentOutput:
    """Mock for making phone calls."""
    print(f" MOCK CALLING AGENT: Received prompt -> '{prompt}'")
    await asyncio.sleep(1)
    return AgentOutput(status="completed", result="Successfully made the call and spoke with the restaurant.")