
import browser_agent
import asyncio

async def test_info1():
    """Test getting business info using the new modular API"""
    result = await browser_agent.get_business_info(
        business_name="Tap House",
        business_website="https://tap-house-munich.de/",
        info_type="opening_hours",
        context_date="2025-09-28",
        context_time="17:00"
    )
    print(f"Result: {result}")

async def test_info2():
    """Test getting business info using the new modular API"""
    import router
    task_data = {
        "business": {
            "name": 'Tap House Munich',
            "website": ""
        },
        "user": {
            "name": "Information Requester",
            "email": "info@example.com"
        },
        "intent": "info",
        "info": {
            "info_type": "pricing", # can be either of pricing, opening_hours, dietary_information, availability
        }
    }
    router = router.get_router()
    result = await router.execute_automation(task_data)
    print(f"Result: {result}")

async def test_info3():
    """Test getting business info using the new modular API"""
    import router
    task_data = {
        "business": {
            "name": 'Tap House Munich',
            "website": ""
        },
        "user": {
            "name": "Information Requester",
            "email": "info@example.com"
        },
        "intent": "info",
        "info": {
            "info_type": "availability", # can be either of pricing, opening_hours, dietary_information, availability
        }
    }
    router = router.get_router()
    result = await router.execute_automation(task_data)
    print(f"Result: {result}")

async def test_info4():
    """Test getting business info using the new modular API"""
    import router
    task_data = {
        "business": {
            "name": 'Tap House Munich',
            "website": ""
        },
        "user": {
            "name": "Information Requester",
            "email": "info@example.com"
        },
        "intent": "info",
        "info": {
            "info_type": "dietary_information", # can be either of pricing, opening_hours, dietary_information, availability
        }
    }
    router = router.get_router()
    result = await router.execute_automation(task_data)
    print(f"Result: {result}")

async def test_reservation1():
    """Test reservation that should fail - restaurant closed on Sundays"""
    result = await browser_agent.make_reservation(
        business_name="Tap House",
        business_website="https://tap-house-munich.de/",
        customer_name="Hans Mueller",
        customer_email="hans@g.com",
        reservation_date="2025-09-28",
        start_time="17:00",
        end_time="18:00",
        party_size=9,
        phone_number="+48123123123",
        duration_minutes=120,
        notes="The reservation is for a birthday party",
        preferences="",
        budget=None
    )
    print(f"Result: {result}")


async def test_reservation2():
    """Test reservation that should fail - too many people (>6)"""
    result = await browser_agent.make_reservation(
        business_name="Haidhauser Augustiner München",
        business_website="",
        customer_name="Heinrich Schmidt",
        customer_email="h@g.com",
        reservation_date="2025-09-27",
        start_time="17:00",
        end_time="18:00",
        party_size=9,
        phone_number="+48123123123",
        duration_minutes=120,
        notes="",
        preferences="",
        budget=None
    )
    print(f"Result: {result}")


async def test_reservation3():
    """Test reservation that should succeed"""
    result = await browser_agent.make_reservation(
        business_name="Augustiner Klosterwirt",
        business_website="https://augustiner-klosterwirt.de/index.php/",
        customer_name="Maria Musterfrau",
        customer_email="h@g.com",
        reservation_date="2025-09-27",
        start_time="19:00",
        end_time="20:00",
        party_size=29,
        phone_number="+48123123123",
        duration_minutes=120,
        notes="",
        preferences="",
        budget=None
    )
    print(f"Result: {result}")

async def test_reservation4():
    """Does not allow online reservations"""
    result = await browser_agent.make_reservation(
        business_name="Lindwurmstüberl",
        business_website="https://www.lindwurmstueberl-muenchen.de/start.html",
        customer_name="Maria Musterfrau",
        customer_email="h@g.com",
        reservation_date="2025-09-27",
        start_time="17:00",
        end_time="18:00",
        party_size=5,
        phone_number="+48123123123",
        duration_minutes=120,
        notes="",
        preferences="",
        budget=None
    )
    print(f"Result: {result}")

async def test_reservation5():
    """Does not allow online reservations"""
    result = await browser_agent.make_reservation(
        business_name="Die Friseure aus Haidhausen",
        business_website="https://www.die-friseure-haidhausen.de/",
        customer_name="Maria Musterfrau",
        customer_email="h@g.com",
        reservation_date="2025-09-27",
        start_time="17:00",
        end_time="18:00",
        party_size=5,
        phone_number="+48123123123",
        duration_minutes=120,
        notes="",
        preferences="",
        budget=None
    )
    print(f"Result: {result}")

async def test_reservation6():
    """Does not allow online reservations"""
    result = await browser_agent.make_reservation(
        business_name="Pater Pane",
        business_website="https://hansimglueck-burgergrill.de/burger-restaurant/muenchen-giesing/",
        customer_name="Maria Musterfrau",
        customer_email="h@g.com",
        reservation_date="2025-09-27",
        start_time="17:00",
        end_time="18:00",
        party_size=5,
        phone_number="+48123123123",
        duration_minutes=120,
        notes="",
        preferences="",
        budget=None
    )
    print(f"Result: {result}")

async def test_recommend1():
    """Test restaurant recommendations using the new modular API"""
    result = await browser_agent.recommend_restaurants(
        user_query="Italian food, vegetarian options, cozy atmosphere",
        area="Munich",
        budget=35
    )
    print(f"Recommendation Result: {result}")

async def test_recommend2():
    """Test restaurant recommendations using the router directly"""
    import router
    task_data = {
        "business": {
            "name": "Restaurant Search in Munich",
            "website": ""
        },
        "user": {
            "name": "Restaurant Seeker",
            "email": "recommendations@example.com"
        },
        "intent": "recommend",
        "recommend": {
            "user_query": "Asian cuisine, spicy food, modern ambiance",
            "area": "Munich city center",
            "budget": 40
        }
    }
    router = router.get_router()
    result = await router.execute_automation(task_data)
    print(f"Direct Router Recommendation Result: {result}")

async def main():
    """Run all tests to demonstrate the new modular API"""
    await test_reservation6()

if __name__ == "__main__":
    asyncio.run(main())
