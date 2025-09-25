#!/usr/bin/env python3
"""
Test script for the Calling Module with Jonas's real phone number.

This script demonstrates how to use the calling module with actual phone numbers
for testing real call scenarios.
"""

import os
import time
from calling_module import start_call
from calling_module.contracts import CallStatus

# Test phone numbers for real call simulation
PHONE_NUMBER_JONAS = "+491706255818"  # Jonas's phone (destination)
PHONE_NUMBER_TWILIO = "+15205953159"  # Our Twilio number (source/callback)

def test_reservation_request():
    """Test a reservation request to Jonas's phone."""
    
    # Example reservation request
    task_data = {
        "business": {
            "phone": PHONE_NUMBER_JONAS,
            "name": "Jonas's Test Restaurant",
            "timezone": "Europe/Berlin"
        },
        "user": {
            "name": "Test User",
            "callback_phone": PHONE_NUMBER_TWILIO  # Our Twilio number for callbacks
        },
        "intent": "reserve",
        "reservation": {
            "date": "2024-01-20",
            "time_window": {
                "start_time": "19:00",
                "end_time": "21:00"
            },
            "party_size": 2,
            "notes": "Birthday dinner"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 4,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("🚀 Starting test call to Jonas's phone...")
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"📋 Task: {task_data['intent']} - {task_data['reservation']['party_size']} people at {task_data['reservation']['time_window']['start_time']}")
    
    try:
        # This will make an actual call if environment variables are set
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        print("💡 Make sure all required fields are provided")
        
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
        print("💡 Check your ElevenLabs API credentials in .env file")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_info_request():
    """Test an info request to Jonas's phone."""
    
    task_data = {
        "business": {
            "phone": PHONE_NUMBER_JONAS,
            "name": "Jonas's Test Restaurant"
        },
        "user": {
            "name": "Test User"
        },
        "intent": "info",
        "info": {
            "question_type": "availability",
            "context": "Looking for availability for 2 people next weekend"
        }
    }
    
    print("\n🚀 Starting info request call...")
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"❓ Question: {task_data['info']['question_type']}")
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def run_single_test(test_name):
    """Run a single test based on command line argument."""
    if test_name == "reservation":
        print("📞 Running RESERVATION REQUEST test only")
        test_reservation_request()
    elif test_name == "info":
        print("📞 Running INFO REQUEST test only")
        test_info_request()
    else:
        print(f"❌ Unknown test: {test_name}")
        print("💡 Available tests: 'reservation', 'info'")
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
        # Run tests sequentially with delays
        print("\n" + "="*50)
        print("🚀 STARTING SEQUENTIAL TEST CALLS")
        print("="*50)
        
        # Test 1: Reservation Request
        print("\n📞 TEST 1: RESERVATION REQUEST")
        print("-" * 30)
        test_reservation_request()
        
        # Wait for first call to complete before starting second
        print("\n⏳ Waiting 30 seconds before second call...")
        print("💡 Complete the first call, then the second will start automatically")
        time.sleep(30)
        
        # Test 2: Info Request
        print("\n📞 TEST 2: INFO REQUEST")
        print("-" * 30)
        test_info_request()
    
    print("\n🎉 Test(s) completed!")
    print("📋 Check your ElevenLabs dashboard for call status and logs")
