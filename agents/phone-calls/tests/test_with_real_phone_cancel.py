#!/usr/bin/env python3
"""
Test script for cancel agent functionality.

Tests three different cancellation scenarios with real phone calls.
"""

import os
import sys
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calling_module import start_call

# Test phone numbers for real call simulation
PHONE_NUMBER_JONAS = "+491706255818"  # Jonas's phone (destination)
PHONE_NUMBER_TWILIO = "+15205953159"  # Our Twilio number (source/callback)


def test_restaurant_cancellation():
    """Test a restaurant reservation cancellation to Jonas's phone."""
    
    task_data = {
        "business": {
            "phone": PHONE_NUMBER_JONAS,
            "name": "Bella Vista Restaurant",
            "timezone": "Europe/Berlin"
        },
        "user": {
            "name": "Maria Schmidt",
            "callback_phone": PHONE_NUMBER_TWILIO
        },
        "intent": "cancel",
        "cancel": {
            "booking_reference": "BV-2024-001",
            "name_on_reservation": "Maria Schmidt",
            "current_date": "2024-01-20",
            "current_time_window": {
                "start_time": "19:00",
                "end_time": "21:00"
            },
            "notes": "Family emergency - need to cancel anniversary dinner",
            "cancellation_reason": "Family emergency"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 3,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("🍽️ RESTAURANT CANCELLATION SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"📋 Booking Reference: {task_data['cancel']['booking_reference']}")
    print(f"📅 Reservation Date: {task_data['cancel']['current_date']} at {task_data['cancel']['current_time_window']['start_time']}")
    print(f"👤 Name on Reservation: {task_data['cancel']['name_on_reservation']}")
    print(f"💬 Reason: {task_data['cancel']['notes']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a restaurant host/hostess handling cancellation requests")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_hotel_cancellation():
    """Test a hotel booking cancellation to Jonas's phone."""
    
    task_data = {
        "business": {
            "phone": PHONE_NUMBER_JONAS,
            "name": "Grand Hotel Berlin",
            "timezone": "Europe/Berlin"
        },
        "user": {
            "name": "James Anderson",
            "callback_phone": PHONE_NUMBER_TWILIO
        },
        "intent": "cancel",
        "cancel": {
            "booking_reference": "GHB-2024-002",
            "name_on_reservation": "James Anderson",
            "current_date": "2024-02-15",
            "current_time_window": {
                "start_time": "15:00",
                "end_time": "17:00"
            },
            "notes": "Business trip canceled due to project postponement - need to cancel hotel stay",
            "cancellation_reason": "Business trip postponed"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 4,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("🏨 HOTEL CANCELLATION SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"📋 Booking Reference: {task_data['cancel']['booking_reference']}")
    print(f"📅 Check-in Date: {task_data['cancel']['current_date']} at {task_data['cancel']['current_time_window']['start_time']}")
    print(f"👤 Name on Reservation: {task_data['cancel']['name_on_reservation']}")
    print(f"💼 Reason: {task_data['cancel']['notes']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a hotel receptionist handling booking cancellations")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_hairdresser_cancellation():
    """Test a hairdresser appointment cancellation to Jonas's phone."""
    
    task_data = {
        "business": {
            "phone": PHONE_NUMBER_JONAS,
            "name": "Style Studio Hair Salon",
            "timezone": "Europe/Berlin"
        },
        "user": {
            "name": "Sarah Johnson",
            "callback_phone": PHONE_NUMBER_TWILIO
        },
        "intent": "cancel",
        "cancel": {
            "booking_reference": "SS-2024-003",
            "name_on_reservation": "Sarah Johnson",
            "current_date": "2024-01-25",
            "current_time_window": {
                "start_time": "14:00",
                "end_time": "16:00"
            },
            "notes": "Sick with flu - need to cancel haircut and highlights appointment",
            "cancellation_reason": "Illness"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 3,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("💇 HAIRDRESSER CANCELLATION SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"📋 Booking Reference: {task_data['cancel']['booking_reference']}")
    print(f"📅 Appointment Date: {task_data['cancel']['current_date']} at {task_data['cancel']['current_time_window']['start_time']}")
    print(f"👤 Name on Reservation: {task_data['cancel']['name_on_reservation']}")
    print(f"🤒 Reason: {task_data['cancel']['notes']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a salon receptionist handling appointment cancellations")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def run_single_test(test_name):
    """Run a single test based on command line argument."""
    if test_name == "restaurant":
        test_restaurant_cancellation()
    elif test_name == "hotel":
        test_hotel_cancellation()
    elif test_name == "hairdresser":
        test_hairdresser_cancellation()
    else:
        print(f"❌ Unknown test: {test_name}")
        print("💡 Available tests: 'restaurant', 'hotel', 'hairdresser'")
        exit(1)


if __name__ == "__main__":
    import sys
    
    print("🚫 Cancel Agent Test Script")
    print("=" * 50)
    
    # Check if environment variables are set
    required_vars = [
        "ELEVENLABS_API_KEY",
        "ELEVENLABS_AGENT_ID", 
        "ELEVENLABS_AGENT_PHONE_NUMBER_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please set these in your .env file before running tests")
        print("📝 See env.example for reference")
        exit(1)
    
    print("✅ All required environment variables are set")
    print(f"📞 Target phone number: {PHONE_NUMBER_JONAS}")
    print(f"📞 From/Callback number: {PHONE_NUMBER_TWILIO}")
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        run_single_test(test_name)
    else:
        # Run all cancellation tests sequentially with delays
        print("\n" + "="*50)
        print("🚀 STARTING ALL CANCELLATION SCENARIOS")
        print("="*50)
        
        # Test 1: Restaurant Cancellation
        print("\n📞 SCENARIO 1: RESTAURANT CANCELLATION")
        print("-" * 40)
        test_restaurant_cancellation()
        
        # Wait between calls
        print("\n⏳ Waiting 30 seconds before next call...")
        print("💡 Complete the first call, then the next will start automatically")
        time.sleep(30)
        
        # Test 2: Hotel Cancellation
        print("\n📞 SCENARIO 2: HOTEL CANCELLATION")
        print("-" * 40)
        test_hotel_cancellation()
        
        # Wait between calls
        print("\n⏳ Waiting 30 seconds before next call...")
        time.sleep(30)
        
        # Test 3: Hairdresser Cancellation
        print("\n📞 SCENARIO 3: HAIRDRESSER CANCELLATION")
        print("-" * 40)
        test_hairdresser_cancellation()
    
    print("\n🎉 Cancellation test(s) completed!")
    print("📋 Check your ElevenLabs dashboard for call status and logs")
