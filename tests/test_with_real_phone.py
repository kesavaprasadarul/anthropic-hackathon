#!/usr/bin/env python3
"""
Test script for the Calling Module with Jonas's real phone number.

This script demonstrates how to use the calling module with actual phone numbers
for testing real call scenarios.
"""

import os
import sys
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calling_module import start_call
from calling_module.contracts import CallStatus

# Test phone numbers for real call simulation
PHONE_NUMBER_JONAS = "+491706255818"  # Jonas's phone (destination)
PHONE_NUMBER_TWILIO = "+15205953159"  # Our Twilio number (source/callback)

def test_restaurant_reservation():
    """Test a restaurant reservation request to Jonas's phone."""
    
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
        "intent": "reserve",
        "reservation": {
            "date": "2024-01-20",
            "time_window": {
                "start_time": "19:00",
                "end_time": "21:00"
            },
            "party_size": 2,
            "notes": "Anniversary dinner for our 5th wedding anniversary",
            "budget_range": "€60–100 per person"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 4,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("🍽️ RESTAURANT RESERVATION SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"📅 Date: {task_data['reservation']['date']} at {task_data['reservation']['time_window']['start_time']}")
    print(f"👥 Party Size: {task_data['reservation']['party_size']}")
    print(f"🎉 Occasion: {task_data['reservation']['notes']}")
    print(f"💰 Budget: {task_data['reservation']['budget_range']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a restaurant host/hostess taking reservations")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_hotel_booking():
    """Test a hotel booking request to Jonas's phone."""
    
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
        "intent": "reserve",
        "reservation": {
            "date": "2024-02-15",
            "time_window": {
                "start_time": "15:00",
                "end_time": "17:00"
            },
            "party_size": 2,
            "notes": "Business trip for tech conference, need quiet room with good WiFi, looking to stay for 2 nights",
            "budget_range": "€120–180 per night"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 5,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("🏨 HOTEL BOOKING SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"📅 Check-in: {task_data['reservation']['date']} at {task_data['reservation']['time_window']['start_time']}")
    print(f"👥 Guests: {task_data['reservation']['party_size']}")
    print(f"💼 Purpose: {task_data['reservation']['notes']}")
    print(f"💰 Budget: {task_data['reservation']['budget_range']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a hotel receptionist taking bookings")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_hairdresser_appointment():
    """Test a hairdresser appointment request to Jonas's phone."""
    
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
        "intent": "reserve",
        "reservation": {
            "date": "2024-01-25",
            "time_window": {
                "start_time": "14:00",
                "end_time": "16:00"
            },
            "party_size": 1,
            "notes": "Haircut and highlights for job interview next week",
            "budget_range": "€80–120 total"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 3,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("💇 HAIRDRESSER APPOINTMENT SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"📅 Date: {task_data['reservation']['date']} at {task_data['reservation']['time_window']['start_time']}")
    print(f"👥 People: {task_data['reservation']['party_size']}")
    print(f"💇 Services: {task_data['reservation']['notes']}")
    print(f"💰 Budget: {task_data['reservation']['budget_range']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a salon receptionist booking appointments")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")




def run_single_test(test_name):
    """Run a single test based on command line argument."""
    if test_name == "restaurant":
        test_restaurant_reservation()
    elif test_name == "hotel":
        test_hotel_booking()
    elif test_name == "hairdresser":
        test_hairdresser_appointment()
    else:
        print(f"❌ Unknown test: {test_name}")
        print("💡 Available tests: 'restaurant', 'hotel', 'hairdresser'")
        exit(1)


if __name__ == "__main__":
    import sys
    
    print("🎯 Calling Module Test Script")
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
        # Run all reservation tests sequentially with delays
        print("\n" + "="*50)
        print("🚀 STARTING ALL RESERVATION SCENARIOS")
        print("="*50)
        
        # Test 1: Restaurant Reservation
        print("\n📞 SCENARIO 1: RESTAURANT RESERVATION")
        print("-" * 40)
        test_restaurant_reservation()
        
        # Wait between calls
        print("\n⏳ Waiting 30 seconds before next call...")
        print("💡 Complete the first call, then the next will start automatically")
        time.sleep(30)
        
        # Test 2: Hotel Booking
        print("\n📞 SCENARIO 2: HOTEL BOOKING")
        print("-" * 40)
        test_hotel_booking()
        
        # Wait between calls
        print("\n⏳ Waiting 30 seconds before next call...")
        time.sleep(30)
        
        # Test 3: Hairdresser Appointment
        print("\n📞 SCENARIO 3: HAIRDRESSER APPOINTMENT")
        print("-" * 40)
        test_hairdresser_appointment()
        
    
    print("\n🎉 Test(s) completed!")
    print("📋 Check your ElevenLabs dashboard for call status and logs")
