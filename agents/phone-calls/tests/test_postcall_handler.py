#!/usr/bin/env python3
"""
Test script for postcall handler functionality.

Simulates webhook payloads from ElevenLabs to test the postcall processing.
"""

import os
import sys
from datetime import datetime, time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calling_module.router import CallingModuleRouter
from calling_module.contracts import CallStatus

def test_postcall_scenarios():
    """Test various postcall scenarios."""
    
    print("🧪 Testing Postcall Handler Scenarios")
    print("=" * 50)
    
    router = CallingModuleRouter()
    
    # Scenario 1: Successful reservation
    print("\n✅ SCENARIO 1: Successful Restaurant Reservation")
    print("-" * 40)
    
    successful_webhook = {
        "call_id": "conv_8801k618xhy1e75t2rx5gw9gqp9",
        "status": "completed",
        "summary": "Successfully booked table for 2 people at Bella Vista Restaurant on January 20, 2024 at 7:30 PM. Booking reference: BV-2024-001. Total cost: $180.",
        "transcript": "Customer: Hi, I'd like to make a reservation. Agent: Hello, I'm calling on behalf of Maria Schmidt for an anniversary dinner. Customer: We have availability at 7:30 PM for 2 people. Agent: Perfect! Can I get a confirmation number? Customer: Yes, your booking reference is BV-2024-001. Total will be $180. Agent: Thank you, confirmed for January 20, 2024 at 7:30 PM for 2 people under Maria Schmidt.",
        "duration_seconds": 180,
        "recording_url": "https://example.com/recording1.mp3",
        "transcript_url": "https://example.com/transcript1.txt"
    }
    
    try:
        result = router.on_postcall(successful_webhook)
        print(f"📋 Status: {result.status.value}")
        print(f"💬 Message: {result.message}")
        print(f"🎯 Next Action: {result.next_action.value}")
        
        if result.core_artifact:
            print(f"📝 Booking Reference: {result.core_artifact.booking_reference}")
            print(f"📅 Confirmed Date: {result.core_artifact.confirmed_date}")
            print(f"⏰ Confirmed Time: {result.core_artifact.confirmed_time}")
            print(f"👥 Party Size: {result.core_artifact.party_size}")
            print(f"💰 Total Cost: {result.core_artifact.total_cost}")
        
        if result.observations:
            print(f"🔄 Alternatives: {result.observations.offered_alternatives}")
            print(f"💳 Payment Methods: {result.observations.payment_methods}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Scenario 2: No availability
    print("\n❌ SCENARIO 2: No Availability")
    print("-" * 40)
    
    no_availability_webhook = {
        "call_id": "conv_8801k618xhy1e75t2rx5gw9gqr",
        "status": "no_availability",
        "summary": "No tables available for requested time. Restaurant is fully booked for January 20, 2024 evening. Alternative times offered: 6:00 PM or 9:30 PM.",
        "transcript": "Customer: I'm sorry, we're fully booked for that evening. Agent: Are there any alternative times? Customer: We have availability at 6:00 PM or 9:30 PM. Agent: I'll check with the customer about these alternatives.",
        "duration_seconds": 120
    }
    
    try:
        result = router.on_postcall(no_availability_webhook)
        print(f"📋 Status: {result.status.value}")
        print(f"💬 Message: {result.message}")
        print(f"🎯 Next Action: {result.next_action.value}")
        
        if result.observations:
            print(f"🔄 Alternatives: {result.observations.offered_alternatives}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Scenario 3: No answer
    print("\n📞 SCENARIO 3: No Answer")
    print("-" * 40)
    
    no_answer_webhook = {
        "call_id": "conv_8801k618xhy1e75t2rx5gw9gqs",
        "status": "no_answer",
        "summary": "Phone rang but no one answered. Business may be closed or unavailable.",
        "transcript": "",
        "duration_seconds": 45
    }
    
    try:
        result = router.on_postcall(no_answer_webhook)
        print(f"📋 Status: {result.status.value}")
        print(f"💬 Message: {result.message}")
        print(f"🎯 Next Action: {result.next_action.value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Scenario 4: Hotel booking with specific requirements
    print("\n🏨 SCENARIO 4: Hotel Booking Success")
    print("-" * 40)
    
    hotel_webhook = {
        "call_id": "conv_8801k618xhy1e75t2rx5gw9gqt",
        "status": "completed",
        "summary": "Successfully booked business suite at Grand Hotel Berlin for James Anderson. Check-in: February 15, 2024 at 3:00 PM. Room includes high-speed WiFi and quiet location. Confirmation code: GHB-2024-002. Rate: €150 per night.",
        "transcript": "Customer: We have a business suite available with high-speed WiFi in a quiet area. Agent: Perfect for our tech conference needs. Customer: Your confirmation code is GHB-2024-002. Rate is €150 per night. Agent: Excellent, confirmed for February 15th check-in at 3:00 PM.",
        "duration_seconds": 240
    }
    
    try:
        result = router.on_postcall(hotel_webhook)
        print(f"📋 Status: {result.status.value}")
        print(f"💬 Message: {result.message}")
        print(f"🎯 Next Action: {result.next_action.value}")
        
        if result.core_artifact:
            print(f"📝 Confirmation Code: {result.core_artifact.confirmation_code}")
            print(f"📅 Check-in Date: {result.core_artifact.confirmed_date}")
            print(f"⏰ Check-in Time: {result.core_artifact.confirmed_time}")
        
        if result.evidence:
            print(f"⏱️ Call Duration: {result.evidence.call_duration_seconds} seconds")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Scenario 5: Hairdresser appointment
    print("\n💇 SCENARIO 5: Hairdresser Appointment Success")
    print("-" * 40)
    
    salon_webhook = {
        "call_id": "conv_8801k618xhy1e75t2rx5gw9gqu",
        "status": "completed",
        "summary": "Appointment confirmed at Style Studio Hair Salon for Sarah Johnson. Date: January 25, 2024 at 2:00 PM. Services: Haircut and highlights. Duration: 2 hours. Total cost: €100. Stylist: Emma (specializes in professional looks for interviews).",
        "transcript": "Customer: We can accommodate Sarah for a cut and highlights on January 25th at 2:00 PM. Agent: Perfect for her job interview next week. Customer: Emma will be her stylist - she's great with professional looks. Total cost is €100 for 2 hours. Agent: Excellent, confirmed for January 25th at 2:00 PM.",
        "duration_seconds": 150
    }
    
    try:
        result = router.on_postcall(salon_webhook)
        print(f"📋 Status: {result.status.value}")
        print(f"💬 Message: {result.message}")
        print(f"🎯 Next Action: {result.next_action.value}")
        
        if result.core_artifact:
            print(f"📅 Appointment Date: {result.core_artifact.confirmed_date}")
            print(f"⏰ Appointment Time: {result.core_artifact.confirmed_time}")
            print(f"💰 Total Cost: {result.core_artifact.total_cost}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def test_postcall_with_real_call_id():
    """Test postcall with a real call ID from our test calls."""
    
    print("\n🔗 Testing Postcall with Real Call ID")
    print("=" * 50)
    
    # Use a call ID that might exist from our test calls
    real_call_webhook = {
        "call_id": "conv_8801k618xhy1e75t2rx5gw9gqp9n",  # From our previous test
        "status": "completed",
        "summary": "Test call completed successfully. Restaurant reservation confirmed for 2 people at 7:00 PM on January 20, 2024. Booking reference: TEST-001.",
        "transcript": "This was a test call to verify the system is working correctly.",
        "duration_seconds": 120
    }
    
    router = CallingModuleRouter()
    
    try:
        result = router.on_postcall(real_call_webhook)
        print(f"📋 Status: {result.status.value}")
        print(f"💬 Message: {result.message}")
        print(f"🎯 Next Action: {result.next_action.value}")
        print(f"🆔 Call ID: {result.call_id}")
        print(f"🔑 Task ID: {result.task_id}")
        print(f"🔐 Idempotency Key: {result.idempotency_key}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Check environment variables
    required_vars = [
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_AGENT_ID", 
        "ELEVENLABS_AGENT_PHONE_NUMBER_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("💡 Make sure your .env file is properly configured")
        sys.exit(1)
    
    print("✅ All required environment variables are set")
    
    # Run tests
    test_postcall_scenarios()
    test_postcall_with_real_call_id()
    
    print("\n🎉 Postcall handler tests completed!")
    print("💡 In production, these webhooks would be sent by ElevenLabs when calls end")
