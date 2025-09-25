# 📞 Test Call Guide

This guide explains how to run the calling module tests with your phone number.

## 🎯 Test Scenarios

### **Test 1: Reservation Request**
- **Your Role**: Restaurant owner/staff at "Jonas's Test Restaurant"
- **AI's Request**: Book table for 2 people on Jan 20, 2024 at 7:00-9:00 PM
- **Special Notes**: "Birthday dinner - testing the calling module"
- **Duration**: Max 4 minutes

### **Available Test Types:**
- **Reservation Agent**: Restaurant, hotel, and hairdresser booking scenarios
- **Reschedule Agent**: Restaurant, hotel, and hairdresser reschedule scenarios  
- **Cancel Agent**: Restaurant, hotel, and hairdresser cancellation scenarios
- **Info Agent**: Restaurant, hotel, and hairdresser information request scenarios

## 🚀 How to Run Tests

### **Reservation Agent Tests**
```bash
# Run specific reservation scenario
python tests/test_with_real_phone.py restaurant
python tests/test_with_real_phone.py hotel
python tests/test_with_real_phone.py hairdresser

# Run all reservation scenarios sequentially
python tests/test_with_real_phone.py
```

### **Reschedule Agent Tests**
```bash
# Run specific reschedule scenario
python tests/test_with_real_phone_reschedule.py restaurant
python tests/test_with_real_phone_reschedule.py hotel
python tests/test_with_real_phone_reschedule.py hairdresser

# Run all reschedule scenarios sequentially
python tests/test_with_real_phone_reschedule.py
```

### **Cancel Agent Tests**
```bash
# Run specific cancel scenario
python tests/test_with_real_phone_cancel.py restaurant
python tests/test_with_real_phone_cancel.py hotel
python tests/test_with_real_phone_cancel.py hairdresser

# Run all cancel scenarios sequentially
python tests/test_with_real_phone_cancel.py
```

### **Info Agent Tests**
```bash
# Run specific info scenario
python tests/test_with_real_phone_info.py restaurant
python tests/test_with_real_phone_info.py hotel
python tests/test_with_real_phone_info.py hairdresser

# Run all info scenarios sequentially
python tests/test_with_real_phone_info.py
```

## ⏰ Call Timing

Each test scenario runs with:
- **Individual Test**: Starts immediately when run
- **Sequential Tests**: 30-second delay between each scenario
- **Typical Duration**: 2-4 minutes per call depending on complexity
- **Gap Between Calls**: 30 seconds when running multiple scenarios

## 📱 What to Expect

### **Caller ID**
- **From**: `+15205953159` (our Twilio number)
- **To**: `+491706255818` (your phone)

### **Call Flow**
1. **Phone rings** with Twilio caller ID
2. **AI introduces itself** as calling for a reservation/info
3. **You respond** as restaurant staff
4. **AI handles** the conversation naturally
5. **Call ends** when task is complete or timeout reached

## 🎭 Role-Playing Tips

### **For Reservation Test**
- ✅ **Accept**: "Yes, we have a table available for 2 people at 7:30 PM"
- ❌ **Decline**: "Sorry, we're fully booked for that time"
- 🔄 **Negotiate**: "We don't have 7 PM, but we have 8 PM available"
- 📝 **Ask questions**: "Do you have any dietary restrictions?"

### **For Different Agent Types**
- ✅ **Reservation**: Accept bookings, suggest alternatives, confirm details
- ✅ **Reschedule**: Help move existing bookings, check availability
- ✅ **Cancel**: Process cancellations, explain policies, provide confirmations
- ✅ **Info**: Provide requested information, answer questions clearly

## 🔧 Troubleshooting

### **If calls don't start**
1. Check your `.env` file has all required variables
2. Verify ElevenLabs API credentials
3. Check Twilio account is linked to ElevenLabs

### **If calls overlap**
- Use single test mode: `python3 test_with_real_phone.py reservation`
- Wait for first call to complete before running second

### **If AI doesn't respond well**
- Speak clearly and naturally
- Give realistic restaurant responses
- Don't be too complex - keep it simple

## 📊 Monitoring

### **ElevenLabs Dashboard**
- Check call status and duration
- Review conversation transcripts
- Monitor call quality and success rates

### **Logs**
- Structured logging shows call attempts
- Error messages for failed calls
- Call ID tracking for debugging

## 🎉 Success Criteria

A successful test should show:
- ✅ Call initiated successfully
- ✅ Call ID returned
- ✅ Natural conversation flow
- ✅ Appropriate call duration
- ✅ Clear call outcome in logs

---

**Ready to test?** Run `python3 test_with_real_phone.py` and answer your phone! 📞
