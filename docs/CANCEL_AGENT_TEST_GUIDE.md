# 🚫 Cancel Agent Test Guide

## 🎯 **Overview**

This guide covers the three distinct cancellation scenarios designed to test Alfred's cancellation capabilities across different booking types and business contexts.

## 🚫 **Cancel Agent Prompt Structure**

The cancel agent uses a focused prompt designed for canceling existing bookings:

### **Key Dynamic Variables:**
- `user_name`: Customer name
- `business_name`: Business name  
- `context_summary`: Brief description (e.g., "Dinner reservation")
- `booking_reference`: Identifier for the existing reservation
- `name_on_reservation`: Name under which the booking was made
- `current_date`: Original reservation date and time
- `notes`: Additional details or preferences

## 🍽️ **Scenario 1: Restaurant Cancellation**

### **Test Command:**
```bash
python3 test_with_real_phone_cancel.py restaurant
```

### **Scenario Details:**
- **Business**: Bella Vista Restaurant
- **Customer**: Maria Schmidt
- **Booking Reference**: BV-2024-001
- **Reservation**: January 20, 2024 at 7:00 PM (2 people)
- **Reason**: Family emergency - need to cancel anniversary dinner

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of Maria Schmidt. I'd like to cancel an existing reservation at Bella Vista Restaurant."

### **Role for Jonas:**
🎭 **Play as a restaurant host/hostess handling cancellation requests**
- Ask for booking reference or confirmation details
- Verify the reservation details
- Process the cancellation
- Inform about any cancellation policies or fees
- Provide cancellation confirmation number

---

## 🏨 **Scenario 2: Hotel Cancellation**

### **Test Command:**
```bash
python3 test_with_real_phone_cancel.py hotel
```

### **Scenario Details:**
- **Business**: Grand Hotel Berlin
- **Customer**: James Anderson
- **Booking Reference**: GHB-2024-002
- **Reservation**: February 15, 2024 at 3:00 PM check-in
- **Reason**: Business trip canceled due to project postponement

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of James Anderson. I'd like to cancel an existing reservation at Grand Hotel Berlin."

### **Role for Jonas:**
🎭 **Play as a hotel receptionist handling booking cancellations**
- Verify the booking reference
- Check cancellation policies
- Process the hotel booking cancellation
- Explain any cancellation fees or refund policies
- Provide cancellation confirmation

---

## 💇 **Scenario 3: Hairdresser Cancellation**

### **Test Command:**
```bash
python3 test_with_real_phone_cancel.py hairdresser
```

### **Scenario Details:**
- **Business**: Style Studio Hair Salon
- **Customer**: Sarah Johnson
- **Booking Reference**: SS-2024-003
- **Appointment**: January 25, 2024 at 2:00 PM
- **Services**: Haircut and highlights
- **Reason**: Sick with flu - need to cancel appointment

### **Expected Alfred Opening:**
> "Hello, this is Alfred calling on behalf of Sarah Johnson. I'd like to cancel an existing reservation at Style Studio Hair Salon."

### **Role for Jonas:**
🎭 **Play as a salon receptionist handling appointment cancellations**
- Verify the appointment reference
- Check cancellation policies (24-hour notice, etc.)
- Process the appointment cancellation
- Explain rescheduling options if applicable
- Provide cancellation confirmation

---

## 🚀 **Running Tests**

### **Individual Test:**
```bash
# Test specific scenario
python3 test_with_real_phone_cancel.py restaurant
python3 test_with_real_phone_cancel.py hotel
python3 test_with_real_phone_cancel.py hairdresser
```

### **All Scenarios (Sequential):**
```bash
# Run all tests with 30-second delays
python3 test_with_real_phone_cancel.py
```

**Note**: Sequential tests run all 3 cancellation scenarios with 30-second delays between calls. Complete each call before the next one starts.

## 🎭 **Role-Playing Tips for Jonas**

### **Restaurant Host:**
- Be understanding about cancellations due to emergencies
- Ask for booking reference or name/date to find reservation
- Check cancellation policies (24-hour notice, fees, etc.)
- Process cancellation and provide confirmation number
- Be empathetic about family emergencies

### **Hotel Receptionist:**
- Be professional with business travelers
- Verify booking details carefully
- Check hotel cancellation policies
- Explain refund timelines and any fees
- Offer to reschedule if appropriate

### **Salon Receptionist:**
- Be understanding about illness-related cancellations
- Check salon cancellation policies (24-hour notice)
- Explain any fees for late cancellations
- Offer to reschedule when customer is feeling better
- Be friendly and accommodating

## 📊 **Testing Objectives**

### **For Each Scenario, Test:**
1. **Clear Identification**: Does Alfred identify the existing booking correctly?
2. **Professional Opening**: Is the opening concise and clear?
3. **Information Handling**: Does Alfred provide booking reference and reservation details?
4. **Policy Inquiry**: Does Alfred ask about cancellation policies and fees?
5. **Final Confirmation**: Does Alfred provide complete cancellation summary?

## 🔍 **What to Look For**

### **Success Indicators:**
- ✅ Alfred opens with clear, concise introduction
- ✅ Booking reference is provided when available
- ✅ Reservation details are clearly communicated
- ✅ Cancellation policies are inquired about
- ✅ Complete cancellation summary before ending

### **Potential Issues:**
- ❌ Unclear booking identification
- ❌ Missing booking reference
- ❌ Not asking about cancellation policies
- ❌ Incomplete confirmation process
- ❌ Unprofessional tone

## 📋 **Expected Conversation Flow**

### **Typical Flow:**
1. **Opening**: Alfred identifies himself and states purpose
2. **Identification**: Business asks for booking details
3. **Details**: Alfred provides reference, name, current date
4. **Verification**: Business confirms reservation details
5. **Cancellation**: Business processes the cancellation
6. **Policies**: Business explains any fees or policies
7. **Confirmation**: Alfred provides complete cancellation summary
8. **Closing**: Cancellation confirmation details provided

### **Example Complete Flow:**
```
Alfred: "Hello, this is Alfred calling on behalf of Maria Schmidt. I'd like to cancel an existing reservation at Bella Vista Restaurant."

Host: "Sure, what's the booking reference?"

Alfred: "The booking reference is BV-2024-001. It's for January 20th at 7:00 PM for 2 people under the name Maria Schmidt."

Host: "I can see that reservation. It's for an anniversary dinner. I'm sorry to hear you need to cancel. Since it's within 24 hours, there will be a $25 cancellation fee."

Alfred: "That's understood. Just to confirm: the reservation at Bella Vista Restaurant on January 20, 2024 at 7:00 PM, under the name Maria Schmidt (reference BV-2024-001), has been canceled. Is that correct? Do you have a cancellation number?"

Host: "Yes, confirmed. Your cancellation number is BV-CANCEL-2024-001."

Alfred: "Thank you very much. Have a good day."
```

## 🎉 **Expected Outcomes**

Each scenario should demonstrate Alfred's ability to:
1. **Clearly identify** existing bookings using references
2. **Present reservation details** accurately
3. **Handle business responses** professionally
4. **Inquire about policies** and fees appropriately
5. **Confirm cancellations** completely before ending

## 🔄 **Agent Selection Verification**

The cancel agent should be correctly selected:
- **Agent ID**: `agent_5001k61fbr1mef0t83d74hpvvvtw`
- **Agent Name**: "cancel"
- **Phone Assignment**: Phone number should be assigned to cancel agent before call

This comprehensive testing approach ensures Alfred can handle diverse real-world cancellation scenarios effectively! 🚀
