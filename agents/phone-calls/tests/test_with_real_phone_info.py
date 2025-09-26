#!/usr/bin/env python3
"""
Test script for info agent functionality.

Tests three different information request scenarios with real phone calls.
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


def test_restaurant_info():
    """Test a restaurant availability check to Jonas's phone."""
    
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
        "intent": "info",
        "info": {
            "question_type": "availability",
            "context": "Looking for dinner reservation for 2 people next weekend",
            "specific_date": "2024-01-27",
            "party_size": 2,
            "notes": "Anniversary dinner - prefer romantic table"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 3,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("🍽️ RESTAURANT INFO REQUEST SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"❓ Question Type: {task_data['info']['question_type']}")
    print(f"📅 Specific Date: {task_data['info']['specific_date']}")
    print(f"👥 Party Size: {task_data['info']['party_size']}")
    print(f"💬 Context: {task_data['info']['context']}")
    print(f"📝 Notes: {task_data['info']['notes']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a restaurant host/hostess handling availability inquiries")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_hotel_info():
    """Test a hotel policy inquiry to Jonas's phone."""
    
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
        "intent": "info",
        "info": {
            "question_type": "policies",
            "context": "Need to understand cancellation and pet policies for business trip",
            "notes": "Traveling with small dog and need flexible booking for work schedule"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 4,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("🏨 HOTEL INFO REQUEST SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"❓ Question Type: {task_data['info']['question_type']}")
    print(f"💬 Context: {task_data['info']['context']}")
    print(f"📝 Notes: {task_data['info']['notes']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a hotel receptionist handling policy inquiries")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def test_hairdresser_info():
    """Test a salon pricing inquiry to Jonas's phone."""
    
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
        "intent": "info",
        "info": {
            "question_type": "price",
            "context": "Need pricing for haircut and highlights for job interview preparation",
            "notes": "First time client, want to know package deals and individual service prices"
        },
        "locale": "en-US",
        "policy": {
            "autonomy_level": "medium",
            "max_call_duration_minutes": 3,
            "allow_payment_info": False,
            "allow_personal_details": True
        }
    }
    
    print("💇 HAIRDRESSER INFO REQUEST SCENARIO")
    print("=" * 50)
    print(f"📞 Calling: {PHONE_NUMBER_JONAS}")
    print(f"📞 From: {PHONE_NUMBER_TWILIO}")
    print(f"🏢 Business: {task_data['business']['name']}")
    print(f"👤 Customer: {task_data['user']['name']}")
    print(f"❓ Question Type: {task_data['info']['question_type']}")
    print(f"💬 Context: {task_data['info']['context']}")
    print(f"📝 Notes: {task_data['info']['notes']}")
    print("=" * 50)
    
    try:
        call_id = start_call(task_data)
        print(f"✅ Call initiated successfully!")
        print(f"🆔 Call ID: {call_id}")
        print("📱 Jonas should receive a call shortly...")
        print("🎭 ROLE: Play as a salon receptionist handling pricing inquiries")
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
    except RuntimeError as e:
        print(f"❌ Call initiation failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def run_single_test(test_name):
    """Run a single test based on command line argument."""
    if test_name == "restaurant":
        test_restaurant_info()
    elif test_name == "hotel":
        test_hotel_info()
    elif test_name == "hairdresser":
        test_hairdresser_info()
    else:
        print(f"❌ Unknown test: {test_name}")
        print("💡 Available tests: 'restaurant', 'hotel', 'hairdresser'")
        exit(1)


if __name__ == "__main__":
    import sys
    
    print("ℹ️ Info Agent Test Script")
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
        # Run all info tests sequentially with delays
        print("\n" + "="*50)
        print("🚀 STARTING ALL INFO REQUEST SCENARIOS")
        print("="*50)
        
        # Test 1: Restaurant Info
        print("\n📞 SCENARIO 1: RESTAURANT INFO REQUEST")
        print("-" * 40)
        test_restaurant_info()
        
        # Wait between calls
        print("\n⏳ Waiting 30 seconds before next call...")
        print("💡 Complete the first call, then the next will start automatically")
        time.sleep(30)
        
        # Test 2: Hotel Info
        print("\n📞 SCENARIO 2: HOTEL INFO REQUEST")
        print("-" * 40)
        test_hotel_info()
        
        # Wait between calls
        print("\n⏳ Waiting 30 seconds before next call...")
        time.sleep(30)
        
        # Test 3: Hairdresser Info
        print("\n📞 SCENARIO 3: HAIRDRESSER INFO REQUEST")
        print("-" * 40)
        test_hairdresser_info()
    
    print("\n🎉 Info request test(s) completed!")
    print("📋 Check your ElevenLabs dashboard for call status and logs")
