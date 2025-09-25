# Phone Number Configuration

This document outlines the phone numbers used in the Calling Module for real-world testing.

## 📞 Phone Numbers

### **Destination Number (Jonas's Phone)**
- **Number**: `+491706255818`
- **Purpose**: The phone number that receives the outbound calls
- **Location**: Germany
- **Type**: Mobile phone
- **Usage**: All test scenarios call this number

### **Source/Callback Number (Our Twilio Account)**
- **Number**: `+15205953159`
- **Purpose**: The phone number that initiates calls and receives callbacks
- **Location**: United States
- **Type**: Twilio phone number
- **Usage**: 
  - `from_number` in outbound calls
  - `callback_phone` for user callbacks
  - Default in configuration

## 🔧 Configuration

### **Environment Variables**
```bash
# Your actual Twilio number (linked to ElevenLabs)
TWILIO_FROM_NUMBER=+15205953159

# Other required variables
ELEVENLABS_API_KEY=your_api_key
ELEVENLABS_AGENT_ID=your_agent_id
ELEVENLABS_AGENT_PHONE_NUMBER_ID=your_phone_number_id
```

### **Test Constants**
```python
# In tests/test_calling_module.py and test_with_real_phone.py
PHONE_NUMBER_JONAS = "+491706255818"  # Destination
PHONE_NUMBER_TWILIO = "+15205953159"  # Source/Callback
```

### **Default Configuration**
The system automatically uses `+15205953159` as the default `from_number` if `TWILIO_FROM_NUMBER` is not set in the environment.

## 📋 Call Flow

```
ElevenLabs Agent → +15205953159 (our Twilio) → +491706255818 (Jonas's phone)
                                                      ↓
User Callbacks ← +15205953159 (our Twilio) ← +491706255818 (Jonas's phone)
```

## 🧪 Testing

### **Run Tests**
```bash
# Run all tests with real phone numbers
python3 -m pytest tests/ -v

# Run real phone test script
python3 test_with_real_phone.py
```

### **Expected Behavior**
1. **Outbound calls**: From `+15205953159` to `+491706255818`
2. **Callbacks**: From `+491706255818` to `+15205953159`
3. **Caller ID**: Shows `+15205953159` on Jonas's phone
4. **Webhook data**: Contains both phone numbers for tracking

## 📱 Phone Number Formats Supported

### **German Mobile Numbers**
- `+491706255818` (E.164 format)
- `0170 625 5818` (German mobile with 0)
- `170 625 5818` (German mobile without country code)
- `+49 170 625 5818` (Formatted with spaces)

### **US Twilio Numbers**
- `+15205953159` (E.164 format)
- `5205953159` (US format)
- `(520) 595-3159` (Formatted)

## 🔍 Verification

To verify the configuration is working:

1. **Check constants**:
   ```python
   from test_with_real_phone import PHONE_NUMBER_JONAS, PHONE_NUMBER_TWILIO
   print(f"Jonas: {PHONE_NUMBER_JONAS}")
   print(f"Twilio: {PHONE_NUMBER_TWILIO}")
   ```

2. **Check config defaults**:
   ```python
   from calling_module.config import get_config
   config = get_config()
   print(f"Default from_number: {config.twilio.from_number}")
   ```

3. **Run tests**:
   ```bash
   python3 -m pytest tests/test_calling_module.py::TestOutboundCaller::test_start_call_success -v
   ```

## 🚀 Ready for Production

The calling module is now configured with real phone numbers and ready for:
- ✅ **Real call testing** with your Twilio account
- ✅ **ElevenLabs integration** with proper phone numbers
- ✅ **Callback handling** through your Twilio number
- ✅ **Call tracking** with real call IDs
- ✅ **Error handling** for authentication and rate limits

## 📞 Next Steps

1. Set up your `.env` file with real ElevenLabs credentials
2. Run the test script to make actual calls
3. Monitor call outcomes through ElevenLabs dashboard
4. Test different scenarios (reservations, info requests, cancellations)
5. Debug any issues with structured logging

---

**Note**: These phone numbers are configured for the hackathon project and should be updated for production use.
