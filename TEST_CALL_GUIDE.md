# 📞 Test Call Guide

This guide explains how to run the calling module tests with your phone number.

## 🎯 Test Scenarios

### **Test 1: Reservation Request**
- **Your Role**: Restaurant owner/staff at "Jonas's Test Restaurant"
- **AI's Request**: Book table for 2 people on Jan 20, 2024 at 7:00-9:00 PM
- **Special Notes**: "Birthday dinner - testing the calling module"
- **Duration**: Max 4 minutes

### **Test 2: Info Request**
- **Your Role**: Restaurant owner/staff at "Jonas's Test Restaurant"
- **AI's Request**: Check availability for 2 people next weekend
- **Purpose**: Information gathering
- **Duration**: Shorter call

## 🚀 How to Run Tests

### **Option 1: Run Both Tests Sequentially (Recommended)**
```bash
python3 test_with_real_phone.py
```
**What happens**:
1. First call (Reservation) starts immediately
2. 30-second delay after first call
3. Second call (Info) starts automatically
4. You can take one call at a time

### **Option 2: Run Single Test**
```bash
# Run only the reservation test
python3 test_with_real_phone.py reservation

# Run only the info test
python3 test_with_real_phone.py info
```

## ⏰ Call Timing

| Test | Start Time | Duration | Gap |
|------|------------|----------|-----|
| **Reservation** | Immediate | ~4 minutes | 30 seconds |
| **Info** | After gap | ~2 minutes | - |

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

### **For Info Test**
- ✅ **Provide info**: "We have availability Saturday at 7 PM and Sunday at 6 PM"
- ❌ **Say busy**: "We're fully booked next weekend"
- 🔄 **Ask for details**: "What time are you looking for?"
- 📝 **Give general info**: "We typically book 2-3 weeks in advance"

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
