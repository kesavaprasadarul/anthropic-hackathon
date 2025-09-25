# Jarvis Calling Module

A channel-scoped capability for the Jarvis multi-agent system that enables outbound phone calls to businesses on behalf of users for tasks like reservations, scheduling, cancellations, and availability checks.

## Features

- **Outbound Calling**: Uses ElevenLabs managed agent platform with Twilio integration
- **Real SDK Integration**: Direct integration with [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- **Task Processing**: Supports reservations, rescheduling, cancellations, and info requests
- **Standardized Outcomes**: Maps call results to consistent status vocabulary
- **Mid-call Tools**: Optional webhook endpoints for agent tool requests
- **Observability**: Structured logging and metrics collection
- **Input Validation**: Comprehensive task validation and normalization
- **Error Handling**: Proper handling of ElevenLabs API errors (authentication, rate limits, etc.)

## Project Structure

```
📁 calling_module/           # Core calling module package
📁 tests/                    # All test files (unit + real phone tests)
📁 docs/                     # Documentation and guides
📄 main.py                   # FastAPI application entry point
📄 requirements.txt          # Python dependencies
📄 env.example               # Environment variables template
📄 README.md                 # This file
📄 PHONE_NUMBERS.md          # Phone number configuration
```

See [`docs/PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) for detailed organization.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment file and fill in your credentials:

```bash
cp env.example .env
```

Required environment variables:
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key
- `ELEVENLABS_AGENT_ID`: Your ElevenLabs agent ID
- `ELEVENLABS_AGENT_PHONE_NUMBER_ID`: Your ElevenLabs agent phone number ID

### 3. Run the Service

```bash
python main.py
```

The service will start on `http://localhost:8000`

### 4. API Endpoints

- `POST /start_call` - Initiate an outbound call
- `POST /postcall` - Process post-call webhooks from ElevenLabs
- `POST /tools/{tool_name}` - Mid-call tool webhooks
- `GET /health` - Health check
- `GET /metrics` - Service metrics

## Usage Example

### Starting a Call

```python
import requests

# Reservation request
task_data = {
    "business": {
        "phone": "+1234567890",
        "name": "Test Restaurant",
        "timezone": "America/New_York"
    },
    "user": {
        "name": "John Doe",
        "callback_phone": "+0987654321"
    },
    "intent": "reserve",
    "reservation": {
        "date": "2024-01-15",
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
        "max_call_duration_minutes": 4
    }
}

response = requests.post("http://localhost:8000/start_call", json=task_data)
call_id = response.json()["call_id"]
```

### Processing Post-Call Results

The service automatically processes webhooks from ElevenLabs and returns normalized results:

```python
# Example webhook payload from ElevenLabs
webhook_payload = {
    "call_id": "call_123",
    "status": "completed",
    "summary": "Successfully booked table for 2 people at 19:30",
    "transcript": "Confirmed reservation for John Doe"
}

# Result will be automatically normalized to:
{
    "status": "completed",
    "message": "Successfully completed task. Booking reference: REF123",
    "next_action": "add_to_calendar",
    "core_artifact": {
        "booking_reference": "REF123",
        "confirmed_date": "2024-01-15T00:00:00",
        "confirmed_time": "19:30:00",
        "party_size": 2
    }
}
```

## Status Vocabulary

The module returns standardized status values:

- `completed` - Task succeeded
- `no_availability` - No slots available
- `no_answer` - Business didn't answer
- `voicemail` - Went to voicemail
- `ivr_blocked` - Blocked by IVR system
- `needs_user_input` - Missing required information
- `timeout` - Call duration exceeded
- `error` - Technical failure

## Next Actions

Based on the call outcome, the module suggests next actions:

- `add_to_calendar` - Add confirmed appointment to calendar
- `retry_later` - Retry the call at a different time
- `request_user_input` - Ask user for additional information
- `switch_channel` - Try a different communication channel
- `none` - No specific action needed

## Testing

### Unit Tests
Run the unit test suite with mocks:

```bash
pytest tests/test_calling_module.py
```

### Real Phone Tests
Test with actual phone calls using different agents:

```bash
# Reservation agent tests
python tests/test_with_real_phone.py restaurant
python tests/test_with_real_phone.py hotel
python tests/test_with_real_phone.py hairdresser

# Reschedule agent tests  
python tests/test_with_real_phone_reschedule.py restaurant
python tests/test_with_real_phone_reschedule.py hotel
python tests/test_with_real_phone_reschedule.py hairdresser

# Cancel agent tests
python tests/test_with_real_phone_cancel.py restaurant
python tests/test_with_real_phone_cancel.py hotel
python tests/test_with_real_phone_cancel.py hairdresser

# Info agent tests
python tests/test_with_real_phone_info.py restaurant
python tests/test_with_real_phone_info.py hotel
python tests/test_with_real_phone_info.py hairdresser
```

### Postcall Handler Tests
Simulate webhook scenarios:

```bash
python tests/test_postcall_handler.py
```

See [`docs/`](docs/) for detailed testing guides for each agent type.

## Architecture

The module is designed with clean separation of concerns:

- `contracts.py` - Data structures and interfaces
- `input_adapter.py` - Input validation and normalization
- `payload_builder.py` - Agent metadata preparation
- `outbound_caller.py` - ElevenLabs SDK integration
- `postcall_handler.py` - Outcome processing and normalization
- `router.py` - Public API interface
- `observability.py` - Logging and metrics
- `tool_webhook.py` - Mid-call tool handlers

## Security

- Phone numbers are redacted in logs
- Webhook signature verification (in production)
- PII protection in metadata
- Idempotency keys prevent duplicate calls
- Call duration limits enforced

## Development

### Adding New Tools

To add a new mid-call tool:

1. Add the tool function to `tool_webhook.py`
2. Register it in the `tools` dictionary
3. Add tests for the new tool
4. Update the `/tools` endpoint documentation

### Extending Status Vocabulary

To add new status types:

1. Add the status to `CallStatus` enum in `contracts.py`
2. Add pattern matching in `postcall_handler.py`
3. Update tests with new scenarios
4. Document the new status

## License

This project is part of the Jarvis multi-agent system.
