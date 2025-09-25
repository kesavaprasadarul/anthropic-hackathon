import browser_agent
import datetime
import json
import asyncio

async def test_info1():
    agent = browser_agent.BrowserAgent()
    payload = browser_agent.Envelope(
        target_business=browser_agent.TargetBusiness(name="Tap House", website="https://tap-house-munich.de/"),
        intent=browser_agent.Intent.INFO,
        intent_payload=browser_agent.InfoPayload(
            info_type=browser_agent.InfoType.OPENING_HOURS,
            context_date=datetime.date(2025,9,28),
            context_time=datetime.time(17,0)
        )
    )
    result = await agent.process(payload)
    print(f"Result: {result}")

async def test_reservation1():
    # Note: Should fail as the restaurant is closed on Sundays and no reservations are possible
    agent = browser_agent.BrowserAgent()
    payload = browser_agent.Envelope(
        target_business=browser_agent.TargetBusiness(name="Tap House", website="https://tap-house-munich.de/"),
        intent=browser_agent.Intent.RESERVE,
        intent_payload=browser_agent.ReservePayload(
            name="Hans Mueller",
            date=datetime.date(2025,9,28),
            time_window_start=datetime.time(17,0),
            time_window_end=datetime.time(18,0),
            email="hans@g.com",
            phone_number="+48123123123",
            party_size=9,
            duration_minutes=120,
            notes="The reservation is for a birthday party",
            preferences="",
            budget=None
        )
    )
    result = await agent.process(payload)
    print(f"Result: {result}")

async def test_reservation2():
    # Note: Should fail as only reservations up to 6 people are possible online
    agent = browser_agent.BrowserAgent()
    payload = browser_agent.Envelope(
        target_business=browser_agent.TargetBusiness(name="Haidhauser Augustiner München", website=""),
        intent=browser_agent.Intent.RESERVE,
        intent_payload=browser_agent.ReservePayload(
            name="Heinrich Schmidt",
            date=datetime.date(2025,9,27),
            time_window_start=datetime.time(17,0),
            time_window_end=datetime.time(18,0),
            email="h@g.com",
            phone_number="+48123123123",
            party_size=9,
            duration_minutes=120,
            notes="",
            preferences="",
            budget=None
        )
    )
    result = await agent.process(payload)
    print(f"Result: {result}")

async def test_reservation3():
    # Note: Should succeed
    agent = browser_agent.BrowserAgent()
    payload = browser_agent.Envelope(
        target_business=browser_agent.TargetBusiness(name="Haidhauser Augustiner München", website=""),
        intent=browser_agent.Intent.RESERVE,
        intent_payload=browser_agent.ReservePayload(
            name="Maria Gonzalez",
            date=datetime.date(2025,9,27),
            time_window_start=datetime.time(17,0),
            time_window_end=datetime.time(18,0),
            email="h@g.com",
            phone_number="+48123123123",
            party_size=5,
            duration_minutes=120,
            notes="",
            preferences="",
            budget=None
        )
    )
    result = await agent.process(payload)
    print(f"Result: {result}")

async def main():
    await test_reservation3()

if __name__ == "__main__":
    asyncio.run(main())
